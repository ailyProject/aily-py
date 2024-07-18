"""
等待音设置
"""

from aily import Aily
from aily.tools import speech_to_text, text_to_speech


def record_end_handler(pcm_data):
    # 语音转文字
    text = speech_to_text(pcm_data)
    print("转换后的文字为: {0}".format(text))
    # 调用LLM
    aily.send_message(text)


def invoke_end_handler(data):
    print("回答：{0}".format(data))
    # 文字转语音
    speech_data = text_to_speech(data)
    # 播放语音
    aily.play(speech_data)


aily = Aily(".env")
aily.set_wait_words("./robot_thinking_16k_s16le.mp3")
aily.loop_play_wait_words=True
aily.on_record_end.subscribe(lambda i: record_end_handler(i))
aily.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aily.run()
