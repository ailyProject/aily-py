import os
import speech_recognition as sr
import requests
import json
from loguru import logger
from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(5))
def speech_to_text(audio_file, filename="input.mp3") -> str:
    model = os.environ.get("STT_MODEL")
    key = os.environ.get("STT_KEY")

    if model == "" or key == "":
        raise Exception("Speech recognition model or key is not set")

    if model == "azure":
        try:
            r = sr.Recognizer()
            audio_data = sr.AudioData(audio_file, 16000, 2)

            language = os.environ.get("STT_LANGUAGE", "zh-CN")
            location = os.environ.get("STT_LOCATION", "eastasia")

            res = r.recognize_azure(
                audio_data, key, language=language, location=location
            )
            return res[0]
        except Exception as e:
            logger.error(
                "Could not request results from Azure Speech Recognition service; {0}".format(
                    e
                )
            )
            raise RuntimeError(
                "Could not request results from Azure Speech Recognition service; {0}".format(
                    e
                )
            )
    elif model == "whisper-1":
        try:
            base_url = os.environ.get("LLM_URL", "https://api.openai.com/v1")
            url = "{0}/audio/transcriptions".format(base_url if base_url else os.getenv("LLM_URL"))
            files = {
                "file": (filename, audio_file),
            }
            req_data = {
                "model": "whisper-1",
            }

            headers = {
                "Authorization": "Bearer {0}".format(key),
            }

            res = requests.post(url, data=req_data, files=files, headers=headers)
            if res.status_code != 200:
                raise Exception("Failed to convert speech to text: {0}".format(res.text))
            return json.loads(res.text)['text']
        except Exception as e:
            logger.error("Could not request results from LLM service; {0}".format(e))
            raise RuntimeError(
                "Could not request results from LLM service; {0}".format(e)
            )
    else:
        raise Exception("Speech recognition model is not supported")


# @retry(stop=stop_after_attempt(5))
# def speech_to_text_by_sr(
#     file, key, method="azure", language="zh-CN", location="eastasia"
# ):
#     r = sr.Recognizer()
#     # with sr.AudioFile(file) as source:
#     #     audio = r.record(source)
#     audio_data = sr.AudioData(file, 16000, 2)

#     if method == "azure":
#         try:
#             res = r.recognize_azure(
#                 audio_data, key, language=language, location=location
#             )
#             return res[0]
#         except sr.UnknownValueError:
#             logger.error("Azure Speech Recognition could not understand audio")
#             return None
#         except sr.RequestError as e:
#             logger.error(
#                 "Could not request results from Azure Speech Recognition service; {0}".format(
#                     e
#                 )
#             )
#             return None

#     return None


# @retry(stop=stop_after_attempt(5))
# def speech_to_text(filename, file, base_url=None, api_key=None):
#     url = "{0}/audio/transcriptions".format(
#         base_url if base_url else os.getenv("LLM_URL")
#     )
#     files = {
#         "file": (filename, file),
#     }
#     req_data = {
#         "model": "whisper-1",
#     }

#     headers = {
#         "Authorization": "Bearer {0}".format(
#             api_key if api_key else os.getenv("LLM_KEY")
#         ),
#     }

#     res = requests.post(url, data=req_data, files=files, headers=headers)
#     if res.status_code != 200:
#         raise Exception("Failed to convert speech to text: {0}".format(res.text))
#     return res.text
