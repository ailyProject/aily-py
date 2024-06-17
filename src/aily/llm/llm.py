import tiktoken

from reactivex.subject import Subject
from reactivex.scheduler import ThreadPoolScheduler
from reactivex import operators as ops
from loguru import logger

from .text_generation import TextGeneration
from .vision import Vision


class AilyLLM:
    def __init__(self):
        self._url = ""
        self._key = ""
        self._model = ""
        self._temperature = 0.5
        self._pre_prompt = ""
        self._max_token_length = 1024
        self._custom_invoke = None

        self._tools = []
        self._tool_choice = "auto"

        self._vision_url = self._url
        self._vision_key = self._key
        self._vision_model = self._model

        self._custom_invoke = False
        self._custom_invoke_vision = False

        self._function_calls = {}
        self.chat_records = []

        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error("TickToken encoding error: {0}".format(e))
            self.encoding = None

        self._event = None

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, value):
        self._event = value

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        self._temperature = value

    @property
    def pre_prompt(self):
        return self._pre_prompt

    @pre_prompt.setter
    def pre_prompt(self, value):
        self._pre_prompt = value

    @property
    def max_token_length(self):
        return self._max_token_length

    @max_token_length.setter
    def max_token_length(self, value):
        self._max_token_length = value

    @property
    def custom_invoke(self):
        return self._custom_invoke

    @custom_invoke.setter
    def custom_invoke(self, value):
        self._custom_invoke = value

    @property
    def custom_invoke_vision(self):
        return self._custom_invoke_vision

    @custom_invoke_vision.setter
    def custom_invoke_vision(self, value):
        self._custom_invoke_vision = value

    @property
    def tools(self):
        return self._tools

    @tools.setter
    def tools(self, value):
        self._tools = value

    @property
    def tool_choice(self):
        return self._tool_choice

    @tool_choice.setter
    def tool_choice(self, value):
        self._tool_choice = value

    @property
    def vision_url(self):
        return self._vision_url

    @vision_url.setter
    def vision_url(self, value):
        self._vision_url = value

    @property
    def vision_key(self):
        return self._vision_key

    @vision_key.setter
    def vision_key(self, value):
        self._vision_key = value

    @property
    def vision_model(self):
        return self._vision_model

    @vision_model.setter
    def vision_model(self, value):
        self._vision_model = value

    def count_token(self, text):
        num_tokens = len(self.encoding.encode(text))
        return num_tokens

    def build_prompt(self, messages, max_token_length):
        if self.encoding is None:
            return messages

        if self._pre_prompt:
            current_token_length = self.count_token(self._pre_prompt)
        else:
            current_token_length = 0

        new_messages = []
        for message in reversed(messages):
            if message["msg_type"] == "image":
                continue
            new_message = {"role": message["role"], "content": message["content"]}
            current_token_length += self.count_token(message["content"])
            if "function_call" in message:
                new_message["function_call"] = message["function_call"]
                current_token_length += self.count_token(str(message["function_call"]))
            if current_token_length < max_token_length:
                new_messages.insert(0, new_message)
            else:
                break

        if self._pre_prompt:
            new_messages.insert(0, {"role": "system", "content": self._pre_prompt})

        return new_messages

    def save_content(self, role, content, msg_type="text"):
        self.event.on_next(
            {
                "type": "conversations",
                "data": {"role": role, "content": content, "msg_type": msg_type},
            }
        )
        self.chat_records.append(
            {"role": role, "content": content, "msg_type": msg_type}
        )

    def invoke_text(self, messages):
        if self._custom_invoke:
            self.event.on_next(
                {
                    "type": "on_custom_invoke",
                    "data": {
                        "url": self._url,
                        "api_key": self._key,
                        "model": self._model,
                        "temperature": self._temperature,
                        "messages": messages,
                    },
                }
            )
        else:
            text_generation = TextGeneration(
                self._url,
                self._key,
                self._model,
                self._temperature,
                self._max_token_length,
            )
            if self._tools:
                text_generation.tools = self._tools
            if self._tool_choice:
                text_generation.tool_choice = self._tool_choice
            response = text_generation.invoke(messages)

            return response.to_dict() if not isinstance(response, dict) else response

    def invoke_vision(self, message, image_url):
        if self._custom_invoke_vision:
            self.event.on_next(
                {
                    "type": "on_custom_invoke_vision",
                    "data": {
                        "url": self._vision_url,
                        "api_key": self._vision_key,
                        "message": message,
                        "image_url": image_url,
                        "model": self._vision_model,
                    },
                }
            )
        else:
            vision = Vision(
                self._vision_url,
                self._vision_key,
                self._vision_model,
                self._max_token_length,
            )
            response = vision.invoke(message, image_url)
            return response.to_dict() if not isinstance(response, dict) else response

    def invoke_error(self):
        self.event.on_next({"type": "on_invoke_error", "data": ""})

    def invoke(self, message: dict, invoke_type="text"):
        if invoke_type == "text":
            self.save_content(message["role"], message["content"], "text")
            messages = self.build_prompt(self.chat_records, self.max_token_length)
            response = self.invoke_text(messages)
            if response is None:
                self.invoke_error()
                return
            tool_calls = response["tool_calls"] if "tool_calls" in response else None
            if tool_calls:
                tool_call_id = tool_calls[0]["id"]
                tool_function_name = tool_calls[0]["function"]["name"]
                tool_query_string = tool_calls[0]["function"]["arguments"]

                self.event.on_next(
                    {
                        "type": "on_function_call",
                        "data": {
                            "id": tool_call_id,
                            "name": tool_function_name,
                            "query": tool_query_string,
                        },
                    }
                )

                self._function_calls[tool_call_id] = {"name": tool_function_name}
            else:
                finally_content = response["content"] if "content" in response else ""
                if not finally_content:
                    logger.warning("Finally content is empty")
                else:
                    self.event.on_next(
                        {"type": "on_invoke_end", "data": finally_content}
                    )
                    self.save_content(response["role"], finally_content)
        elif invoke_type == "image":
            last_message = self.chat_records[-1]
            self.save_content(message["role"], message["content"], "image")
            response = self.invoke_vision(last_message["content"], message["content"])
            logger.debug("tool response: {0}".format(response))
            if response is None:
                self.invoke_error()
                return

            self.save_content(response["role"], response["content"])
            self.event.on_next({"type": "on_invoke_end", "data": response["content"]})

    def send_message(self, content):
        # 开始调用事件发起
        self.event.on_next({"type": "on_invoke_start", "data": ""})
        self.invoke({"role": "user", "content": content})

    def tool_reply(self, tool_call_id, content, reply_type="text"):
        if reply_type == "text":
            self.invoke(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": self._function_calls[tool_call_id]["name"],
                    "content": content,
                }
            )
        elif reply_type == "image":
            self.invoke(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": self._function_calls[tool_call_id]["name"],
                    "content": content,
                },
                "image",
            )
        else:
            logger.warning("Unknown reply type: {0}".format(reply_type))

    def clear_chat_records(self):
        self.chat_records.clear()

    def event_handler(self, event):
        logger.info("收到事件：{0}".format(event["type"]))
        if event["type"] == "invoke":
            self.send_message(event["data"])
        elif event["type"] == "reply":
            self.tool_reply(
                event["data"]["call_id"],
                event["data"]["content"],
                event["data"]["reply_type"],
            )
        elif event["type"] == "clear":
            self.clear_chat_records()
        else:
            pass

    def start(self):
        self.event.pipe(ops.observe_on(ThreadPoolScheduler(1))).subscribe(
            self.event_handler
        )
