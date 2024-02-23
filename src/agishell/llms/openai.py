import os
import aiohttp

from typing import List, Dict


class _OpenAI:
    def __init__(self, url=None, api_key=None):
        self.url = url if url else os.getenv("OPENAI_URL")
        self.api_key = api_key if api_key else os.getenv("OPENAI_KEY")
        self.model = "gpt-3.5-turbo"
        self.temperature = 0.5
        self.pre_prompt = None

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


class ChatOpenAI(_OpenAI):
    async def invoke(self, messages: List[Dict]):
        url = "{0}/v1/chat/completions".format(self.url)

        if self.pre_prompt:
            messages.insert(0, {"role": "system", "content": self.pre_prompt})

        req_data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "stream": False,
        }

        headers = {
            'Authorization': 'Bearer {0}'.format(self.api_key),
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=req_data, headers=headers) as res:
                if res.status != 200:
                    raise RuntimeError("Failed to generate completion: {0}".format(await res.text()))
                result = await res.json()
                message = result["choices"][0]["message"]
                return {"content": message["content"], "role": message["role"]}


class Tools(_OpenAI):
    async def audio_transcription_by_data(self, filename, file):
        url = "{0}/v1/audio/transcriptions".format(self.url)
        files = {
            'file': (filename, file),
        }
        req_data = {
            "model": "whisper-1",
        }

        headers = {
            'Authorization': 'Bearer {0}'.format(self.api_key),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=req_data, files=files, headers=headers) as res:
                if res.status != 200:
                    return None
                return await res.text()
