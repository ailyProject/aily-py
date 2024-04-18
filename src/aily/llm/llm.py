import os
import time

import tiktoken

from reactivex.subject import Subject
from openai import OpenAI
from loguru import logger
import threading


class LLMs(threading.Thread):
    def __init__(self, device):
        self.device = device
        self.chat_records = []

        self.url = device.llm_server
        # self.url = "https://braintrustproxy.com/v1"
        self.api_key = device.llm_key
        self.model = device.llm_model_name
        self.temperature = float(device.llm_temperature)
        self.pre_prompt = device.llm_pre_prompt
        self.max_token_length = device.llm_max_token_length
        self.custom_invoke = None

        self.event_queue = device.event_queue
        self.handler_queue = device.llm_invoke_queue

    def set_custom_invoke(self, custom_invoke: callable):
        self.custom_invoke = custom_invoke

    @staticmethod
    def get_text_token_count(text):
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(text))
        return num_tokens

    def build_prompt(self, messages):
        if self.pre_prompt:
            current_token_length = self.get_text_token_count(self.pre_prompt)
        else:
            current_token_length = 0

        new_messages = []
        for message in reversed(messages):
            new_message = {"role": message["role"], "content": message["content"]}
            current_token_length += self.get_text_token_count(message["content"])
            if "function_call" in message:
                new_message["function_call"] = message["function_call"]
                current_token_length += self.get_text_token_count(
                    str(message["function_call"])
                )
            if current_token_length < self.max_token_length:
                new_messages.insert(0, new_message)
            else:
                break

        if self.pre_prompt:
            new_messages.insert(0, {"role": "system", "content": self.pre_prompt})

        return new_messages

    @staticmethod
    def default_invoke(**kwargs):
        client = OpenAI(base_url=kwargs["url"], api_key=kwargs["api_key"])
        response = client.chat.completions.create(
            model=kwargs["model"],
            messages=kwargs["messages"],
            temperature=kwargs["temperature"],
            stream=False,
        )

        return {
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls,
        }

    def invoke(self, url, api_key, model, temperature, messages):
        if self.custom_invoke:
            return self.custom_invoke(
                url=url,
                api_key=api_key,
                model=model,
                temperature=temperature,
                messages=messages,
            )
        return self.default_invoke(
            url=url,
            api_key=api_key,
            model=model,
            temperature=temperature,
            messages=messages,
        )

    def send_message(self, content):
        # 开始调用事件发起
        self.event_queue.put({"type": "on_invoke_start", "data": ""})
        # 获取缓存聊天记录
        messages = self.chat_records
        messages.append({"role": "user", "content": content})
        messages = self.build_prompt(messages)
        response = self.invoke(
            self.url, self.api_key, self.model, self.temperature, messages
        )
        self.chat_records.append(
            {
                "role": response["role"],
                "content": response["content"],
            }
        )

        # TODO function call处理
        self.event_queue.put({"type": "on_invoke_end", "data": response["content"]})

    def clear_chat_records(self):
        self.chat_records.clear()
    
    def run_msg_handler(self):
        for event in iter(self.handler_queue.get, None):
            try:
                if event["type"] == "invoke":
                    self.send_message(event["data"])
                else:
                    pass
            except Exception as e:
                logger.error("LLM invoke error: {0}".format(e))

    def run(self):
        self.run_msg_handler()
