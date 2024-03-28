"""
零一万物
1. 复制目录下的.env_sample为.env
2. 配置.env中的相关参数（大模型使用零一万勿，语音转文字使用Azure)
"""

import os
import time

from aily import AIGC
from aily.tools import speech_to_text_by_sr, text_to_speech, speex_decoder
from dotenv import load_dotenv

load_dotenv()


def record_end_handler(data):
    # 解码pcm, azure语音识别需要wav格式, 所以这里需要指定result_type="wav"
    voice_data = speex_decoder(data, result_type="wav")
    # 语音转文字
    text = speech_to_text_by_sr(voice_data, key=os.getenv("AZURE_KEY"))
    print("转换后的文字为: {0}".format(text))
    # 调用LLM
    aigc.send_message(text)


def invoke_end_handler(data):
    print("回答：{0}".format(data))
    # 文字转语音
    speech_data = text_to_speech(data)
    # 播放语音
    aigc.play(speech_data)


aigc = AIGC(os.getenv("PORT"))
aigc.set_key(os.getenv("LLM_01KEY"))
aigc.set_server(os.getenv("LLM_01URL"))
aigc.set_model("yi-34b-chat-0205")
aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.run()
