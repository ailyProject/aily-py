import serial

from reactivex.scheduler import ThreadPoolScheduler
from reactivex import operators as ops
from loguru import logger


class AilyTTS:
    serial = None

    def __init__(self):
        self._port = ""
        self._baudrate = 0
        self._event = None

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def baudrate(self):
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value):
        self._baudrate = value

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, value):
        self._event = value

    def init(self):
        self.serial = serial.Serial(self.port, self.baudrate)

    def gen_tts_buffer(self, text):
        # 生成语音数据
        buffer_head = [0xFD]
        buffer_cmd = [0x01]
        buffer_encode = [0x04]

        content_bytes = text.encode('utf-8')
        content_length = len(content_bytes)
        buffer_text_length = content_length + 2
        highByte = buffer_text_length >> 8
        lowByte = buffer_text_length & 0xFF
        buffer_length = [highByte, lowByte]

        buffer = bytearray(buffer_head + buffer_length + buffer_cmd + buffer_encode + list(content_bytes))
        return buffer

    def event_handler(self, event):
        event_type = event["type"]

        if event_type == "play_tts_by_aily":
            if not event["data"]:
                return

            logger.debug("Start to play TTS")
            content = self.gen_tts_buffer(event["data"])
            self.serial.write(content)

    def start(self):
        self.event.pipe(
            ops.observe_on(ThreadPoolScheduler(1))
        ).subscribe(lambda i: self.event_handler(i))
