import requests
from loguru import logger
from tenacity import retry, wait_random_exponential, stop_after_attempt


class Vision:
    def __init__(self, url: str, key: str, model: str, max_length: int):
        self._url: str = url
        self._key: str = key
        self._model = model
        self._max_length = max_length

    @retry(
        wait=wait_random_exponential(multiplier=1, max=10), stop=stop_after_attempt(3)
    )
    def invoke(self, message, image_data):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._key}",
            }

            payload = {
                "model": self._model,
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
                                "image_url": image_data,
                            },
                        ],
                    }
                ],
                "max_tokens": self._max_length,
            }

            url = "{0}/chat/completions".format(self._url)

            response = requests.post(url, headers=headers, json=payload)
            logger.debug("Vision Response: {0}".format(response))
            res_data = response.json()
            assistant_message = res_data["choices"][0]["message"] if "choices" in res_data else res_data
            return assistant_message
        except Exception as e:
            logger.error("Vision invoke error: {0}".format(e))
            return None
