import os
from typing import Union
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_random_exponential
from ..models import STTBaiduOptions, STTAzureOptions, STTWhisperOptions
from .tools import stt_baidu, stt_azure, stt_whisper


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=40))
def speech_to_text(
    pcm_data,
    *,
    model: str = None,
    options: Union[STTBaiduOptions, STTAzureOptions, STTWhisperOptions, None] = None,
) -> str:
    if not model:
        model = os.environ.get("STT_MODEL")
    if not model:
        raise Exception("Speech recognition model is not set")

    if model == "baidu":
        if options is None:
            api_key = os.environ.get("STT_KEY")
            secret_key = os.environ.get("STT_SECRET_KEY")
            app_id = os.environ.get("STT_APP_ID", "")
            dev_pid = os.environ.get("STT_DEV_PID", 1537)

            options = STTBaiduOptions(
                key=api_key, secret_key=secret_key, app_id=app_id, dev_pid=int(dev_pid)
            )
            
        logger.debug("options: {0}".format(options))

        return stt_baidu(pcm_data, options=options)
    elif model == "azure":
        if options is None:
            key = os.environ.get("STT_KEY")
            location = os.environ.get("STT_LOCATION", "eastasia")
            lang = os.environ.get("STT_LANG", "zh-CN")

            options = STTAzureOptions(key=key, location=location, lang=lang)

        return stt_azure(pcm_data, options=options)
    elif model == "whisper":
        if options is None:
            key = os.environ.get("STT_KEY")
            url = os.environ.get("STT_URL")

            options = STTWhisperOptions(key=key, url=url)

        return stt_whisper(pcm_data, options=options)
    else:
        raise Exception("Speech recognition model is not supported")


# @retry(stop=stop_after_attempt(5))
# def speech_to_text(audio_file, filename="input.wav", model=None, key=None, language=None, location=None) -> str:

#     if model is None:
#         model = os.environ.get("STT_MODEL")
#     if key is None:
#         key = os.environ.get("STT_KEY")

#     if not model or not key:
#         raise Exception("Speech recognition model or key is not set")

#     r = sr.Recognizer()
#     audio_data = sr.AudioData(audio_file, 16000, 2)

#     if model == "azure":
#         try:
#             language = os.environ.get("STT_LANGUAGE") or "zh-CN"
#             location = os.environ.get("STT_LOCATION") or "eastasia"

#             res = r.recognize_azure(
#                 audio_data, key, language=language, location=location
#             )
#             return res[0]
#         except Exception as e:
#             logger.error(
#                 "Could not request results from Azure Speech Recognition service; {0}".format(
#                     e
#                 )
#             )
#             return None
#     elif model == "whisper-1":
#         try:
#             base_url = os.environ.get("STT_URL") or "https://api.openai.com/v1"
#             client = openai.OpenAI(base_url=base_url, api_key=key)

#             wav_data = BytesIO(audio_data.get_wav_data())
#             wav_data.name = filename
#             res = client.audio.transcriptions.create(file=wav_data, model=model)
#             return res.text
#         except Exception as e:
#             logger.error("Could not request results from LLM service; {0}".format(e))
#             # raise RuntimeError(
#             #     "Could not request results from LLM service; {0}".format(e)
#             # )
#             return None
#     else:
#         raise Exception("Speech recognition model is not supported")
