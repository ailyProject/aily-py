"""
自定义模型调用示例，以智普AI为例
需要安装智普SDK: pip install zhipuai
"""

from aily import Aily
from zhipuai import ZhipuAI
from aily.tools import speech_to_text, text_to_speech, speex_decoder
from loguru import logger


def invoke(data):
    client = ZhipuAI(api_key=data["api_key"])
    response = client.chat.completions.create(
        model=data["model"],
        messages=data["messages"],
        temperature=data["temperature"],
    )

    result = {
        "role": response.choices[0].message.role,
        "content": response.choices[0].message.content,
        "tool_calls": response.choices[0].message.tool_calls
    }

    aily.invoke_reply(result)


def record_end_handler(data):
    voice_data = speex_decoder(data, )
    # 语音转文字
    text = speech_to_text(voice_data)
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
aily.on_custom_invoke.subscribe(lambda i: invoke(i))
aily.run()
