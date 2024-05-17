import asyncio
import os
import edge_tts
import tempfile
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import OpenAI
from loguru import logger


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=40))
def text_to_speech(text, output_file=None, model=None, key=None, voice=None) -> bytes:
    model = model or os.environ.get("TTS_MODEL")
    key = key or os.environ.get("TTS_KEY")

    if not model:
        raise Exception("Text to speech model is not set")

    if not output_file:
        output_file = tempfile.gettempdir() + "/output.mp3"

    if model == "edge":
        try:
            role = voice or os.environ.get("TTS_ROLE") or "zh-CN-XiaoxiaoNeural"
            communicate = edge_tts.Communicate(text, role)
            asyncio.run(communicate.save(output_file))
        except Exception as e:
            logger.error(
                "Could not request results from Edge TTS service; {0}".format(e)
            )
            raise RuntimeError(
                "Could not request results from Edge TTS service; {0}".format(e)
            )
    elif model == "tts-1":
        try:
            role = voice or os.environ.get("TTS_ROLE") or "alloy"
            client = OpenAI(base_url=os.environ.get("TTS_URL"), api_key=key)
            res = client.audio.speech.create(
                model=model,
                voice=role,
                input=text,
            )
            res.stream_to_file(output_file)
        except Exception as e:
            logger.error("Could not request results from LLM service; {0}".format(e))
            raise RuntimeError(
                "Could not request results from LLM service; {0}".format(e)
            )
    else:
        raise Exception("Text to speech model is not supported")

    with open(output_file, "rb") as f:
        return f.read()
