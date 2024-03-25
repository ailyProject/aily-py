import requests
from tenacity import retry, stop_after_attempt, wait_random_exponential
from loguru import logger


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=40))
def text_to_speech(text, voice="zh-CN-XiaoxiaoNeural"):
    url = "http://101.34.93.13:7979/tts"
    data = {
        "content": text,
        "voice": voice
    }

    try:
        response = requests.request("POST", url, json=data)
        if response.status_code != 200:
            raise RuntimeError("Failed to request: {0}".format(response.text))

        return response.content
    except Exception as e:
        logger.error("Failed to request: {0}".format(e))
        raise e
