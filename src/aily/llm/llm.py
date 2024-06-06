import os
import time

import tiktoken
import requests

from reactivex.subject import Subject
from openai import OpenAI
from loguru import logger

from tenacity import retry, wait_random_exponential, stop_after_attempt


class LLMs:
    chat_records = []

    def __init__(self):
        self._llm_url = ""
        self._llm_key = ""
        self._llm_model = ""
        self._llm_temperature = 0.5
        self._llm_pre_prompt = ""
        self._llm_max_token_length = 1024
        self._llm_custom_invoke = None

        self._llm_tools = []
        self._llm_tool_choice = "auto"

        self._llm_vision_url = self._llm_url
        self._llm_vision_key = self._llm_key
        self._llm_vision_model = self._llm_model

        self.chat_records = []

    @property
    def llm_url(self):
        return self._llm_url

    @llm_url.setter
    def llm_url(self, value):
        self._llm_url = value

    @property
    def llm_key(self):
        return self._llm_key

    @llm_key.setter
    def llm_key(self, value):
        self._llm_key = value

    @property
    def llm_model(self):
        return self._llm_model

    @llm_model.setter
    def llm_model(self, value):
        self._llm_model = value

        # self.url = device.llm_server
        # self.api_key = device.llm_key
        # self.model = device.llm_model_name
        # self.temperature = float(device.llm_temperature)
        # self.pre_prompt = device.llm_pre_prompt
        # self.max_token_length = device.llm_max_token_length
        # self.custom_invoke = None
        #
        # self.vision_url = device.llm_vision_server
        # self.vision_model = device.llm_vision_model_name
        # self.vision_key = device.llm_vision_key
        #
        # self.tools = device.llm_tools
        # self.tool_choice = device.llm_tool_choice
        #
        # self.function_calls = {}
        #
        # self.event_queue = device.event_queue
        # self.handler_queue = device.llm_invoke_queue
        # self.cache_queue = device.cache_queue
        # try:
        #     self.encoding = tiktoken.get_encoding("cl100k_base")
        # except Exception as e:
        #     logger.error("Ticktoken encoding error: {0}".format(e))
        #     self.encoding = None

    def set_custom_invoke(self, custom_invoke: callable):
        self.custom_invoke = custom_invoke

    def get_text_token_count(self, text):
        num_tokens = len(self.encoding.encode(text))
        return num_tokens

    def build_prompt(self, messages):
        if self.encoding is None:
            return messages

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

    @retry(
        wait=wait_random_exponential(multiplier=1, max=10), stop=stop_after_attempt(3)
    )
    def chat_completion_request(self, **kwargs):
        client = OpenAI(base_url=kwargs["url"], api_key=kwargs["api_key"])

        try:
            response = client.chat.completions.create(
                model=kwargs["model"],
                messages=kwargs["messages"],
                temperature=kwargs["temperature"],
                max_tokens=kwargs["max_token_length"],
                stream=False,
                tools=kwargs["tools"],
                tool_choice=kwargs["tool_choice"],
            )

            return response.choices[0].message
        except Exception as e:
            logger.error(f"LLM调用异常: {e}")
            raise e

    @retry(
        wait=wait_random_exponential(multiplier=1, max=10), stop=stop_after_attempt(3)
    )
    def chat_vision_request(self, message, image_url, model):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.vision_key}",
            }

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": message,
                            },
                            {
                                "type": "image_url",
                                "image_url": image_url,
                            },
                        ],
                    }
                ],
                "max_tokens": self.max_token_length,
            }

            url = "{0}/chat/completions".format(self.vision_url)

            # logger.debug("vision request: {0}".format(payload))

            response = requests.post(url, headers=headers, json=payload)

            # logger.debug("vision response: {0}".format(response.content))

            assistant_message = response.json()["choices"][0]["message"]
            # logger.debug("assistant_message:", assistant_message)
            return assistant_message
        except Exception as e:
            raise e

    def default_invoke(self, **kwargs):
        response_message = self.chat_completion_request(**kwargs)
        return {
            "role": response_message.role,
            "content": response_message.content,
            "tool_calls": response_message.tool_calls,
        }

    def invoke(self, url, api_key, model, temperature, messages):
        if self.custom_invoke:
            return self.custom_invoke(
                url=url,
                api_key=api_key,
                model=model,
                temperature=temperature,
                messages=messages,
                max_token_length=self.max_token_length,
            )
        return self.default_invoke(
            url=url,
            api_key=api_key,
            model=model,
            temperature=temperature,
            messages=messages,
            max_token_length=self.max_token_length,
            tools=self.tools,
            tool_choice=self.tool_choice,
        )

    def save_content(self, role, content):
        self.chat_records.append({"role": role, "content": content})
        self.cache_queue.put(
            {
                "type": "conversations",
                "data": [
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    role,
                    content,
                ],
            }
        )

    def send_message(self, content):
        # 开始调用事件发起
        self.event_queue.put({"type": "on_invoke_start", "data": ""})
        # 获取缓存聊天记录
        current_msg = {"role": "user", "content": content}
        self.save_content(current_msg["role"], current_msg["content"])
        messages = self.build_prompt(self.chat_records)
        # messages = self.chat_records
        # messages.append(current_msg)
        # messages = self.build_prompt(messages)
        start_time = time.time()
        response = self.invoke(
            self.url, self.api_key, self.model, self.temperature, messages
        )
        logger.debug("LLM response time: {0}".format(time.time() - start_time))

        tool_calls = response["tool_calls"]
        if tool_calls:
            tool_call_id = tool_calls[0].id
            tool_function_name = tool_calls[0].function.name
            tool_query_string = tool_calls[0].function.arguments

            self.device.on_function_call.on_next(
                {
                    "id": tool_call_id,
                    "name": tool_function_name,
                    "query": tool_query_string,
                }
            )

            self.function_calls[tool_call_id] = {"name": tool_function_name}

            # 查找self.function_calls中是否有对应的tool_function_name
            # if tool_function_name in self.function_calls:
            #     tool = self.function_calls[tool_function_name]
            # else:
            #     logger.error(f"未找到对应的tool_function_name: {tool_function_name}")
            #     raise Exception(f"未找到对应的tool_function_name: {tool_function_name}")

            # tool_res = tool["func"](tool_query_string)
            # if tool["return_type"] == "image":
            #     pass
            # else:
            #     self.chat_records.append(
            #         {
            #             "role": "tool",
            #             "tool_call_id": tool_call_id,
            #             "name": tool_function_name,
            #             "content": tool_res,
            #         }
            #     )

            #     messages = self.build_prompt(self.chat_records)
            #     response_with_function_call = self.invoke(
            #         self.url, self.api_key, self.model, self.temperature, messages
            #     )

            #     self.save_content(
            #         response_with_function_call["role"],
            #         response_with_function_call["content"],
            #     )
            #     finally_content = response_with_function_call["content"]
        else:
            finally_content = response["content"]
            self.event_queue.put({"type": "on_invoke_end", "data": finally_content})
            self.save_content(response["role"], finally_content)

    def tool_reply(self, tool_call_id, content, reply_type="text"):
        logger.debug("tool_call_id: {0}".format(tool_call_id))
        logger.debug("function calls: {0}".format(self.function_calls))
        last_message = self.chat_records[-1]
        self.chat_records.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": self.function_calls[tool_call_id]["name"],
                "content": content,
            }
        )
        # messages = self.build_prompt(self.chat_records)

        logger.debug("message: {0}".format(last_message))
        if reply_type == "image":
            response = self.chat_vision_request(
                last_message["content"], content, self.vision_model
            )
        else:
            response = self.invoke(
                self.url, self.api_key, self.model, self.temperature, last_message
            )

        logger.debug("tool response: {0}".format(response))

        self.save_content(response["role"], response["content"])
        self.event_queue.put({"type": "on_invoke_end", "data": response["content"]})
        # try:
        #     logger.debug("tool_call_id: {0}".format(tool_call_id))
        #     logger.debug("function calls: {0}".format(self.function_calls))
        #     self.chat_records.append(
        #         {
        #             "role": "tool",
        #             "tool_call_id": tool_call_id,
        #             "name": self.function_calls[tool_call_id]["name"],
        #             "content": content,
        #         }
        #     )
        #     messages = self.build_prompt(self.chat_records)
        #     if reply_type == "image":
        #         response = self.chat_vision_request(
        #             messages[-1]["content"], content, self.vision_model
        #         )
        #     else:
        #         response = self.invoke(
        #             self.url, self.api_key, self.model, self.temperature, messages
        #         )
        #     self.save_content(response["role"], response["content"])
        #     self.event_queue.put({"type": "on_invoke_end", "data": response["content"]})
        # except Exception as e:
        #     logger.error(f"工具调用异常: {e}")

    def clear_chat_records(self):
        self.chat_records.clear()

    def run(self):
        while True:
            event = self.handler_queue.get()

            if event["type"] == "invoke":
                self.send_message(event["data"])
            elif event["type"] == "reply":
                self.tool_reply(event["data"]["call_id"], event["data"]["content"], event["data"]["reply_type"])
            else:
                pass
