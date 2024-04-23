"""
零一万物
"""

import os
import time

from aily.aigc import AIGC
from aily.tools import speech_to_text, text_to_speech, speex_decoder


def record_end_handler(data):
    # 解码pcm
    print("解码: {0}".format(int(time.time())))
    video_data = speex_decoder(data, result_type="wav")
    print("解码结束: {0}".format(int(time.time())))
    # 语音转文字
    print("语音转文字: {0}".format(int(time.time())))
    text = speech_to_text(video_data)
    print("识别到语音: {0}{1}".format(text, int(time.time())))
    # 调用LLM
    print("发起LLM调用: {0}".format(int(time.time())))
    aigc.send_message(text)


def invoke_end_handler(data):
    print("回答：{0}".format(data))
    # 文字转语音
    speech_data = text_to_speech(data)
    # 播放语音
    aigc.play(speech_data)


aigc = AIGC(".env")
aigc.set_wait_words("./robot_thinking_16k_s16le.mp3")

aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.run()
