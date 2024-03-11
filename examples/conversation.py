import os
import time

from agishell.aigc import AIGC
from agishell.tools import speech_to_text_by_sr, text_to_speech, speex_decoder
from dotenv import load_dotenv

load_dotenv()

aigc = AIGC('COM4')
aigc.set_key(os.getenv("OPENAI_KEY"))
aigc.set_server(os.getenv("OPENAI_URL"))
aigc.set_conversation_mode("single")
aigc.set_temp(0.5)
aigc.init()


def event_handler(event):
    if event["type"] == "on_record_end":
        print("录音结束")
        # 解码pcm
        print("开始解码: {0}".format(int(time.time())))
        pcm_data = speex_decoder(event["data"])
        with open("record_data.wav", "wb") as f:
            f.write(pcm_data)
        print("解码结束: {0}".format(int(time.time())))
        # 语音转文字
        print("开始转换语音为文字: {0}".format(int(time.time())))
        text = speech_to_text_by_sr(pcm_data, os.getenv("AZURE_KEY"))
        print("转换语音为文字结束: {0}".format(int(time.time())))
        print("转换后的文字为: {0}".format(text))

        if not text:
            # 未识别到语音
            # speech_text = "抱歉，我没有听清楚，请再说一遍"
            # speech_data = text_to_speech(speech_text)
            # aigc.play(speech_data)
            print("未识别到语音")
            pass
        else:
            # 调用LLM
            aigc.send_message(text)
    elif event["type"] == "wakeup":
        print("唤醒")
    elif event["type"] == "on_invoke_start":
        print("开始调用大模型： {0}".format(int(time.time())))
    elif event["type"] == "on_invoke_end":
        print("大模型调用结束： {0}".format(int(time.time())))
        print("回答：{0}".format(event["data"]))
        # 文字转语音
        print("开始转换文字为语音: {0}".format(int(time.time())))
        speech_data = text_to_speech(event["data"])
        print("转换文字为语音结束: {0}".format(int(time.time())))
        with open("output.mp3", "wb") as f:
            f.write(speech_data)

        # 播放语音
        aigc.play(speech_data)
    else:
        print(event)


aigc.event.subscribe(lambda i: event_handler(i))
aigc.run()
