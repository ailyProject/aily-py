from openai import OpenAI
from loguru import logger
from tenacity import retry, wait_random_exponential, stop_after_attempt
from typing import List, Any


class TextGeneration:
    def __init__(self, url: str, key: str, model: str, temperature: float, max_length: int):
        self._url: str = url
        self._key: str = key
        self._model = model
        self._temperature = temperature
        self._max_length = max_length

        self._tools: List = []
        self._tool_choice: Any = "auto"

        self._stream = False

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
    def stream(self):
        return self._stream

    @stream.setter
    def stream(self, value):
        self._stream = value

    @retry(
        wait=wait_random_exponential(multiplier=1, max=10), stop=stop_after_attempt(3)
    )
    def invoke(self, messages: List):
        try:
            client = OpenAI(base_url=self._url, api_key=self._key)
            data = {
                "model": self._model,
                "temperature": self._temperature,
                "max_tokens": self._max_length,
                "stream": self._stream,
            }
            
            if self._tools:
                data["tools"] = self._tools
                data["tool_choice"] = self._tool_choice
            
            response = client.chat.completions.create(**data, messages=messages)

            logger.debug("Text Generation Response: {0}".format(response))

            return True, response.choices[0].message
        except Exception as e:
            logger.error("Text Generation Error: {0}".format(e))
            return False, str(e)
