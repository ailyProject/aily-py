from aily import Aily
from loguru import logger
from aily.tools import speech_to_text, text_to_speech


def record_end_handler(pcm_data):
    # 语音转文字
    text = speech_to_text(pcm_data)
    logger.debug("转换后的文字为: {0}".format(text))
    # 调用LLM
    aily.send_message(text)


def invoke_end_handler(data):
    logger.debug("回答：{0}".format(data))
    # 文字转语音
    speech_data = text_to_speech(data)
    # 播放语音
    aily.play(speech_data)


aily = Aily(".env")
aily.on_record_end.subscribe(lambda i: record_end_handler(i))
aily.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aily.run()
