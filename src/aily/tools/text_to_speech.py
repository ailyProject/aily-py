import asyncio
import os
import edge_tts
import tempfile
from tenacity import retry, stop_after_attempt, wait_random_exponential
from typing import Union
from openai import OpenAI
from loguru import logger

from ..models import TTSAzureOptions, TTSEdgeOptions, TTSOpenAIOptions, TTSBaiduOptions
from .tools import tts_baidu, tts_openai, tts_edge, tts_azure


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=40))
def text_to_speech(
    text,
    *,
    model=None,
    options=Union[
        TTSBaiduOptions, TTSOpenAIOptions, TTSEdgeOptions, TTSAzureOptions, None
    ]
) -> bytes:
    if not model:
        model = os.environ.get("TTS_MODEL")
    if not model:
        raise Exception("Text to speech model is not set")
    
    if model == "baidu":
        if options is None:
            api_key = os.environ.get("TTS_KEY")
            secret_key = os.environ.get("TTS_SECRET_KEY")
            app_id = os.environ.get("TTS_APP_ID")
            lang = os.environ.get("TTS_LANG")
            options = TTSBaiduOptions(
                key=api_key, secret_key=secret_key, app_id=app_id, lang=lang
            )
        return tts_baidu(text, options)
    elif model == "edge":
        if options is None:
            voice = os.environ.get("TTS_ROLE")
            options = TTSEdgeOptions(voice=voice)
        return tts_edge(text, options=options)
    elif model == "tts-1":
        if options is None:
            key = os.environ.get("TTS_KEY")
            voice = os.environ.get("TTS_ROLE")
            url = os.environ.get("TTS_URL")
            response_format = os.environ.get("TTS_RESPONSE_FORMAT")
            options = TTSOpenAIOptions(
                key=key, voice=voice, url=url, response_format=response_format
            )
        return tts_openai(text, options=options)
    elif model == "azure":
        if options is None:
            key = os.environ.get("TTS_KEY")
            location = os.environ.get("TTS_LOCATION")
            lang = os.environ.get("TTS_LANG")
            voice = os.environ.get("TTS_ROLE")
            options = TTSAzureOptions(
                key=key, location=location, lang=lang, voice=voice
            )
        return tts_azure(text, options=options)
    else:
        raise Exception("Text to speech model is not supported")


# @retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=40))
# def text_to_speech(text, output_file=None, model=None, key=None, voice=None) -> bytes:
#     model = model or os.environ.get("TTS_MODEL")
#     key = key or os.environ.get("TTS_KEY")

#     if not model:
#         raise Exception("Text to speech model is not set")

#     if not output_file:
#         output_file = tempfile.gettempdir() + "/output.mp3"

#     if model == "edge":
#         try:
#             role = voice or os.environ.get("TTS_ROLE") or "zh-CN-XiaoxiaoNeural"
#             communicate = edge_tts.Communicate(text, role)
#             asyncio.run(communicate.save(output_file))
#         except Exception as e:
#             logger.error(
#                 "Could not request results from Edge TTS service; {0}".format(e)
#             )
#             raise RuntimeError(
#                 "Could not request results from Edge TTS service; {0}".format(e)
#             )
#     elif model == "tts-1":
#         try:
#             role = voice or os.environ.get("TTS_ROLE") or "alloy"
#             client = OpenAI(base_url=os.environ.get("TTS_URL"), api_key=key)
#             res = client.audio.speech.create(
#                 model=model,
#                 voice=role,
#                 input=text,
#             )
#             res.stream_to_file(output_file)
#         except Exception as e:
#             logger.error("Could not request results from LLM service; {0}".format(e))
#             raise RuntimeError(
#                 "Could not request results from LLM service; {0}".format(e)
#             )
#     else:
#         raise Exception("Text to speech model is not supported")

#     with open(output_file, "rb") as f:
#         return f.read()
