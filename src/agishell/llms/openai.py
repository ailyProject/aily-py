import os
import aiohttp
import tiktoken

from typing import List, Dict


class OpenAI:
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
    
    def get_text_token_count(text):
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc)
        
    def build_prompt(self, messages):
        model_name = self.model
        if model_name == "gpt-3.5-turbo":
            max_token_length = 4096 - 1024
        elif model_name == "gpt-3.5-turbo-1106":
            max_token_length = 16384 - 4096
        elif model_name == "gpt-4-1106-preview":
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

        with aiohttp.ClientSession() as session:
            res = session.post(url, json=req_data, headers=headers)
            if res.status != 200:
                raise RuntimeError("Failed to generate completion: {0}".format(res.text()))
            result = res.json()
            message = result["choices"][0]["message"]
            return {"content": message["content"], "role": message["role"]}
    

    async def audio_transcription(self, filename, file):
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
