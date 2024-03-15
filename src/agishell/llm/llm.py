import os
import tiktoken

from reactivex.subject import Subject
from openai import OpenAI
from loguru import logger


class LLMs:
    event = Subject()

    def __init__(self, event, url, api_key, model, pre_prompt, temperature=0.5, max_token_length=16384):
        self.aigc_event = event
        self.chat_records = []

        self.url = url
        # self.url = "https://braintrustproxy.com/v1"
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.pre_prompt = pre_prompt
        self.max_token_length = max_token_length
        self.custom_invoke = None

        if self.aigc_event:
            self.aigc_event.subscribe(lambda i: self.event_handler(i))

    def event_handler(self, event):
        if event["type"] == "send_message":
            self._send_message(event["data"])
        elif event["type"] == "clear_chat_records":
            self._clear_chat_records()
        else:
            logger.warning("Unknown event type: {0}".format(event["type"]))

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
            new_message = {
                "role": message["role"],
                "content": message["content"]
            }
            current_token_length += self.get_text_token_count(message["content"])
            if "function_call" in message:
                new_message["function_call"] = message["function_call"]
                current_token_length += self.get_text_token_count(str(message["function_call"]))
            if current_token_length < self.max_token_length:
                new_messages.insert(0, new_message)
            else:
                break

        if self.pre_prompt:
            new_messages.insert(0, {"role": "system", "content": self.pre_prompt})

        return new_messages

    @staticmethod
    def default_invoke(url, api_key, model, temperature, messages):
        client = OpenAI(base_url=url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=False
        )

        return {
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls
        }

    def invoke(self, url, api_key, model, temperature, messages):
        if self.custom_invoke:
            return self.custom_invoke(url, api_key, model, temperature, messages)
        return self.default_invoke(url, api_key, model, temperature, messages)

    def _send_message(self, content):
        # 开始调用事件发起
        self.event.on_next({"type": "on_invoke_start", "data": ""})
        # 获取缓存聊天记录
        messages = self.chat_records
        messages.append({"role": "user", "content": content})
        messages = self.build_prompt(messages)
        response = self.invoke(self.url, self.api_key, self.model, self.temperature, messages)
        self.chat_records.append({
            "role": response["role"],
            "content": response["content"],
        })

        # TODO function call处理

        self.event.on_next({"type": "on_invoke_end", "data": response["content"]})
        return response["content"]
        # 结束调用事件发起

    def _clear_chat_records(self):
        self.chat_records.clear()
