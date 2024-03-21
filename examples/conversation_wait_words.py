"""
零一万物
"""

import os
import time

from agishell.aigc import AIGC
from agishell.tools import speech_to_text_by_sr, text_to_speech, speex_decoder
from dotenv import load_dotenv

load_dotenv()

aigc = AIGC(os.getenv("PORT"))
aigc.set_key(os.getenv("LLM_01KEY"))
aigc.set_server(os.getenv("LLM_01URL"))
aigc.set_pre_prompt(os.getenv("PRE_PROMPT"))
aigc.set_model("yi-34b-chat-0205")
aigc.set_temp(0.5)
# aigc.set_wait_words("收到，让我稍微思考一下")
aigc.set_wait_words("D:\\temp\\robot_thinking_16k_s16le.mp3")
# aigc.set_wwords_auto_play(False)
# aigc.init()


def event_handler(event):
    print("envet: {0}".format(event["type"]))
    if event["type"] == "on_record_end":
        time.sleep(10)
        # 解码pcm
        print("解码: {0}".format(int(time.time())))
        pcm_data = speex_decoder(event["data"])
        with open("record_data.wav", "wb") as f:
            f.write(pcm_data)
        print("解码结束: {0}".format(int(time.time())))
        # 语音转文字
        print("语音转文字: {0}".format(int(time.time())))
        text = speech_to_text_by_sr(pcm_data, os.getenv("AZURE_KEY"))
        # text = custom_speech_to_text(pcm_data)
        print("识别到语音: {0}{1}".format(text, int(time.time())))
        if not text:
            print("未识别到语音")
            pass
        else:
            # 调用LLM
            print("发起LLM调用: {0}".format(int(time.time())))
            aigc.send_message(text)
    elif event["type"] == "on_invoke_end":
        # print("大模型调用结束： {0}".format(int(time.time())))
        # print("回答：{0}".format(event["data"]))
        # 文字转语音
        # print("开始转换文字为语音: {0}".format(int(time.time())))
        speech_data = text_to_speech(event["data"])
        # print("转换文字为语音结束: {0}".format(int(time.time())))
        # with open("output.mp3", "wb") as f:
        #     f.write(speech_data)

        # 播放语音
        aigc.play(speech_data)
    else:
        pass


aigc.event.subscribe(event_handler)
aigc.run()
