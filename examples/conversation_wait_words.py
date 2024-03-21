"""
零一万物
"""

import os
import time

from agishell.aigc import AIGC
from agishell.tools import speech_to_text_by_sr, text_to_speech, speex_decoder
from dotenv import load_dotenv

load_dotenv()


def record_end_handler(data):
    # 解码pcm
    print("解码: {0}".format(int(time.time())))
    video_data = speex_decoder(data, result_type="wav")
    print("解码结束: {0}".format(int(time.time())))
    # 语音转文字
    print("语音转文字: {0}".format(int(time.time())))
    text = speech_to_text_by_sr(video_data, os.getenv("AZURE_KEY"))
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


aigc = AIGC(os.getenv("PORT"))
aigc.set_key(os.getenv("LLM_01KEY"))
aigc.set_server(os.getenv("LLM_01URL"))
aigc.set_pre_prompt(os.getenv("PRE_PROMPT"))
aigc.set_model("yi-34b-chat-0205")
aigc.set_temp(0.5)
aigc.set_wait_words("./robot_thinking_16k_s16le.mp3")

aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.run()
