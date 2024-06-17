import serial
from aily import Aily

from aily.tools import speex_decoder, speech_to_text
from loguru import logger


def record_end_handler(data):
    voice_data = speex_decoder(data)
    text = speech_to_text(voice_data)
    logger.info("转换后的文字为: {0}".format(text))
    aily.send_message(text)


def invoke_end_handler(data):
    logger.info("回答：{0}".format(data))
    aily.play(data)


aily = Aily(".env")
aily.set_wait_words("./robot_thinking_16k_s16le.mp3")
aily.set_wwords_loop_play(True)
aily.use_aily_tts = True
aily.tts_port = "/dev/ttyACM0"
aily.tts_baudrate = 115200
aily.on_record_end.subscribe(lambda i: record_end_handler(i))
aily.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aily.run()
