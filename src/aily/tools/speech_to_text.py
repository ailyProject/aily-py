import os
import requests
import speech_recognition as sr

from loguru import logger
from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(5))
def speech_to_text_by_sr(file, key, method="azure", language="zh-CN", location="eastasia"):
    r = sr.Recognizer()
    # with sr.AudioFile(file) as source:
    #     audio = r.record(source)
    audio_data = sr.AudioData(file, 16000, 2)

    if method == "azure":
        try:
            res = r.recognize_azure(audio_data, key, language=language, location=location)
            return res[0]
        except sr.UnknownValueError:
            logger.error("Azure Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error("Could not request results from Azure Speech Recognition service; {0}".format(e))
            return None

    return None


@retry(stop=stop_after_attempt(5))
def speech_to_text(filename, file, base_url=None, api_key=None):
    url = "{0}/audio/transcriptions".format(base_url if base_url else os.getenv("LLM_URL"))
    files = {
        'file': (filename, file),
    }
    req_data = {
        "model": "whisper-1",
    }

    headers = {
        'Authorization': 'Bearer {0}'.format(api_key if api_key else os.getenv("LLM_KEY")),
    }

    res = requests.post(url, data=req_data, files=files, headers=headers)
    if res.status_code != 200:
        raise Exception("Failed to convert speech to text: {0}".format(res.text))
    return res.text
