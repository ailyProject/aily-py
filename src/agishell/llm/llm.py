import os
import tiktoken

from reactivex.subject import Subject
from openai import OpenAI


class LLMs:
    event = Subject()

    def __init__(self, event=None, url=None, api_key=None, model=None, temperature=None, pre_prompt=None):
        self.aigc_event = event
        self.chat_records = []

        # self.url = url if url else os.getenv("OPENAI_URL")
        self.url = "https://braintrustproxy.com/v1"
        self.api_key = api_key if api_key else os.getenv("OPENAI_KEY")
        self.model = model if model else "gpt-3.5-turbo"
        self.temperature = temperature if temperature else 0.5
        self.pre_prompt = pre_prompt if pre_prompt else None

        if self.aigc_event:
            self.aigc_event.subscribe(lambda i: self.event_handler(i))

    def event_handler(self, event):
        if event["type"] == "wakeup":
            self.clear_chat_records()
        elif event["type"] == "send_message":
            self.send_message(event["data"])

    def set_key(self, key):
        self.api_key = key

    def set_model(self, model_name):
        self.model = model_name

    def set_server(self, url):
        self.url = url

    def set_temp(self, temperature):
        self.temperature = temperature

    def set_pre_prompt(self, pre_prompt):
        self.pre_prompt = pre_prompt

    def check_conf(self):
        if not self.url:
            raise ValueError("OpenAI URL is not set")
        if not self.api_key:
            raise ValueError("OpenAI API Key is not set")

    def get_text_token_count(self, text):
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(text))
        return num_tokens

    def build_prompt(self, messages):
        if self.model == "gpt-3.5-turbo":
            max_token_length = 4096 - 1024
        elif self.model == "gpt-3.5-turbo-1106":
            max_token_length = 16384 - 4096
        elif self.model == "gpt-4-1106-preview":
            max_token_length = 127999 - 4096
        else:
            raise ValueError("Invalid model name")

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
            if current_token_length < max_token_length:
                new_messages.insert(0, new_message)
            else:
                break

        if self.pre_prompt:
            new_messages.insert(0, {"role": "system", "content": self.pre_prompt})

        return new_messages

    def send_message(self, content):
        # 获取缓存聊天记录
        messages = self.chat_records
        messages.append({"role": "user", "content": content})

        self.check_conf()
        client = OpenAI(base_url=self.url, api_key=self.api_key)

        # 开始调用事件发起
        self.event.on_next({"type": "invoke_start", "data": ""})

        messages = self.build_prompt(messages)
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            stream=False
        )

        self.chat_records.append({
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content
        })

        # 结束调用事件发起
        self.event.on_next({"type": "invoke_end", "data": response.choices[0].message.content})

        return response.choices[0].message.content

    def clear_chat_records(self):
        self.chat_records.clear()
