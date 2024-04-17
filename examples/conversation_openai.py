import os
from aily import AIGC
from aily.tools import speech_to_text, text_to_speech, speex_decoder


def record_end_handler(data):
    # 解码pcm
    voice_data = speex_decoder(data)
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
aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.run()
