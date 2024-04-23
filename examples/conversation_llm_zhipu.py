"""
智普AI对话模型调用示例
需要安装智普SDK: pip install zhipuai
"""
import os
import time

from aily import AIGC
from zhipuai import ZhipuAI
from dotenv import load_dotenv
from aily.tools import speech_to_text, text_to_speech, speex_decoder

load_dotenv()


def custom_invoke(**kwargs):
    client = ZhipuAI(api_key=kwargs["api_key"])
    response = client.chat.completions.create(
        model=kwargs["model"],
        messages=kwargs["messages"],
        temperature=kwargs["temperature"],
    )

    return {
        "role": response.choices[0].message.role,
        "content": response.choices[0].message.content,
        "tool_calls": response.choices[0].message.tool_calls
    }


def record_end_handler(data):
    # 解码pcm, azure语音识别需要wav格式, 所以这里需要指定result_type="wav"
    voice_data = speex_decoder(data, result_type="wav")
    # 语音转文字
    text = speech_to_text(voice_data)
    print("转换后的文字为: {0}".format(text))
    # 调用LLM
    aigc.send_message(text)


def invoke_end_handler(data):
    print("回答：{0}".format(data))
    # 文字转语音
    speech_data = text_to_speech(data)
    # 播放语音
    aigc.play(speech_data)


aigc = AIGC(".env")
aigc.set_custom_llm_invoke(custom_invoke)

aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.run()
