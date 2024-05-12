import os
import speech_recognition as sr
import requests
import json
import openai
from io import BytesIO
from loguru import logger
from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(5))
def speech_to_text(audio_file, filename="input.wav", model=None, key=None, language=None, location=None) -> str:
    
    if model is None:
        model = os.environ.get("STT_MODEL")
    if key is None:
        key = os.environ.get("STT_KEY")

    if not model or not key:
        raise Exception("Speech recognition model or key is not set")
    
    r = sr.Recognizer()
    audio_data = sr.AudioData(audio_file, 16000, 2)

    if model == "azure":
        try:
            language = os.environ.get("STT_LANGUAGE") or "zh-CN"
            location = os.environ.get("STT_LOCATION") or "eastasia"

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
            return None
    elif model == "whisper-1":
        try:
            base_url = os.environ.get("STT_URL") or "https://api.openai.com/v1"
            client = openai.OpenAI(base_url=base_url, api_key=key)
            
            wav_data = BytesIO(audio_data.get_wav_data())
            wav_data.name = filename
            res = client.audio.transcriptions.create(file=wav_data, model=model)
            return res.text
        except Exception as e:
            logger.error("Could not request results from LLM service; {0}".format(e))
            # raise RuntimeError(
            #     "Could not request results from LLM service; {0}".format(e)
            # )
            return None
    else:
        raise Exception("Speech recognition model is not supported")
