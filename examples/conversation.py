import os

from agishell.aigc import AIGC
from agishell.tools import speech_to_text, text_to_speech
from dotenv import load_dotenv

load_dotenv()

aigc = AIGC('COM4')
aigc.set_temp(0.5)
aigc.init()


def event_handler(event):
    if event["type"] == "on_record_end":
        print("录音结束")
        # 语音转文字
        text = speech_to_text("record_data.mp3", event["data"])
        print("转换后的文字为: {0}".format(text))
        # 调用LLM
        aigc.send_message(text)
    elif event["type"] == "wakeup":
        print("唤醒")
    elif event["type"] == "invoke_end":
        print("大模型调用结束")
        print("回答：{0}".format(event["data"]))
        # 文字转语音
        speech_data = text_to_speech(event["data"])
        # 播放语音
        aigc.play(speech_data)
    else:
        print(event)


aigc.event.subscribe(lambda i: event_handler(i))
aigc.run()
