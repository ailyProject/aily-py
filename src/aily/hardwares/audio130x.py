import struct
import asyncio
import threading
import time
import os

import serial

from reactivex.subject import Subject
from loguru import logger
from ..tools.speex_decoder import speex_decoder


class DataHead:
    HEAD_MAGIC = 0
    HEAD_CHECKSUM = 1
    HEAD_TYPE = 2
    HEAD_LEN = 3
    HEAD_VERSION = 4
    HEAD_FILL_DATA = 5


class FillCode:
    DEF_FILL = 0x12345678
    INVAILD_SPEAK = 0x12345666
    TTS_FILL = 0x12345677
    MP3_FILL = 0x12345688
    M4A_FILL = 0x123456AA
    REPEAT_FILL = 0x123456AB
    WAV_FILL = 0x123456BB
    NO_WAKE_FILL = 0x0


class TypeCode:
    DEVICE_SLEEP = 0x0000
    LOCAL_ASR_NOTIFY = 0x0101
    WAKE_UP = 0x0102
    VAD_END = 0x0103
    SKIP_INVAILD_SPEAK = 0x0104
    PCM_MIDDLE = 0x0105
    PCM_FINISH = 0x0106
    PCM_IDLE = 0x0107
    NET_PLAY_START = 0x0201
    NET_PLAY_PAUSE = 0x0202
    NET_PLAY_RESUME = 0x0203
    NET_PLAY_STOP = 0x0204
    NET_PLAY_RESTART = 0x0205
    NET_PLAY_NEXT = 0x0206
    NET_PLAY_LOCAL_TTS = 0x0207
    NET_PLAY_END = 0x0208
    NET_PLAY_RECONECT_URL = 0x0209
    PLAY_DATA_GET = 0x020A
    PLAY_DATA_RECV = 0x020B
    PLAY_DATA_END = 0x020C
    PLAY_TTS_END = 0x020D
    PLAY_EMPTY = 0x020E
    PLAY_NEXT = 0x020F
    PLAYING_TTS = 0x0210
    PLAY_RESUME_ERRO = 0x0211
    PLAY_LAST = 0x0212
    QCLOUD_IOT_CMD = 0x0301
    NET_VOLUME = 0x0302
    LOCAL_VOLUME = 0x0303
    VOLUME_INC = 0x0304
    VOLUME_DEC = 0x0305
    VOLUME_MAXI = 0x0306
    VOLUME_MINI = 0x0307
    ENTER_NET_CONFIG = 0x0401
    NET_CONFIGING = 0x0402
    EXIT_NET_CONFIG = 0x0403
    INIT_SMARTCONFIG = 0x0404
    WIFI_DISCONNECTED = 0x0405
    WIFI_CONNECTED = 0x0406
    GET_PROFILE = 0x0407
    NEED_PROFILE = 0x0408
    CLOUD_CONNECTED = 0x0409
    CLOUD_DISCONNECTED = 0x040A
    NET_CONFIG_SUCCESS = 0x040B
    NET_CONFIG_FAIL = 0x040C
    CIAS_OTA_START = 0x0501
    CIAS_OTA_DATA = 0x0502
    CIAS_OTA_SUCESS = 0x0503
    CIAS_FACTORY_START = 0x0504
    CIAS_FACTORY_OK = 0x0505
    CIAS_FACTORY_FAIL = 0x0506
    CIAS_FACTORY_SELF_TEST_START = 0x0507
    CIAS_IR_DATA = 0x0508
    CIAS_IR_LOADING_DATA = 0x0509
    CIAS_IR_LOAD_DATA_OVER = 0x050A
    CIAS_IR_LOAD_DATA_START = 0x050B
    CIAS_CJSON_DATA = 0x0601
    CIAS_SIGNLE_WAKEUP = 0x0701
    CIAS_PHYSICAL_WAKEUP = 0x0702
    CIAS_CONTINUOUS_WAKEUP = 0x0703


class MediaState:
    MEDIA_IDLE = 0x00
    MEDIA_PCM_SEND = 0x01
    MEDIA_MP3_GET = 0x02
    MEDIA_MP3_CHECK = 0x03
    MEDIA_MP3_PLAY = 0x04
    MEDIA_MP3_PAUSE = 0x05


MEDIA_READ_LENGTH = 1024
STANDARD_HEAD_LEN = 16
MAGIC_DATA = 0x5A5AA5A5
CHECK_SUM = 0x00


class AudioModule(threading.Thread):
    event = Subject()

    def __init__(self, device):
        super(AudioModule, self).__init__()

        self.daemon = True

        self.device = device
        self.port = device.port
        self.baud = device.baudrate
        self.serial = None
        self.running = True

        self.audio_event_queue = device.event_queue

        self.state = TypeCode.DEVICE_SLEEP
        # self.prev_state = TypeCode.DEVICE_SLEEP
        self.media_state = TypeCode.DEVICE_SLEEP
        self.conversation_mode = TypeCode.CIAS_SIGNLE_WAKEUP

        self.format_string = "IHHHHI"
        self.read_length = STANDARD_HEAD_LEN
        self.pcm_data = bytearray()
        self.decode_data = bytes()
        self.media_data = bytes()
        self.media_read_start = 0
        self.media_read_end = MEDIA_READ_LENGTH
        self.media_count = 0
        self.process_media_data = bytes()

        self.cmd_action = {
            TypeCode.WAKE_UP: self.wakeup,
            TypeCode.LOCAL_ASR_NOTIFY: self.local,
            TypeCode.PCM_MIDDLE: self.record,
            TypeCode.PCM_FINISH: self.upload,
            TypeCode.PLAY_DATA_GET: self.media,
            TypeCode.PLAY_DATA_RECV: self.media,
            TypeCode.NET_PLAY_END: self.media_end,
        }

        self.lasted_event = ""

        start_data = "A5 A5 5A 5A 00 00 01 02 00 00 00 00 77 56 34 12"
        head_data = "A5 A5 5A 5A 00 00 0A 02 00 00 00 00 77 56 34 12"
        end_data = "A5 A5 5A 5A 00 00 0C 02 00 00 00 00 77 56 34 12"
        stop_data = "A5 A5 5A 5A 00 00 0D 02 00 00 00 00 77 56 34 12"
        hex_values = start_data.split()
        self.start_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.NET_PLAY_START, 0, 0, FillCode.MP3_FILL
        )
        self.head_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.PLAY_DATA_GET, 0, 0, FillCode.MP3_FILL
        )
        self.end_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.PLAY_DATA_END, 0, 0, FillCode.MP3_FILL
        )
        self.stop_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.NET_PLAY_STOP, 0, 0, FillCode.MP3_FILL
        )
        # self.single_byte_data = self.protocol_head_pack(MAGIC_DATA, CHECK_SUM, TypeCode.CIAS_SIGNLE_WAKEUP, 0, 0,
        #                                                 FillCode.DEF_FILL)

        self.file_code = FillCode.MP3_FILL

        # 订阅aigc发出得事件
        # self.aigc_event.subscribe(lambda i: self.event_handler(i))

    def update_fill_code(self, fill_code):
        self.start_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.NET_PLAY_START, 0, 0, fill_code
        )
        self.head_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.PLAY_DATA_GET, 0, 0, fill_code
        )
        self.end_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.PLAY_DATA_END, 0, 0, fill_code
        )
        self.stop_byte_data = self.protocol_head_pack(
            MAGIC_DATA, CHECK_SUM, TypeCode.NET_PLAY_STOP, 0, 0, fill_code
        )
        self.file_code = fill_code

    def protocol_head_pack(
        self, magic, checksum, head_type, data_len, version, fill_data
    ):
        head_data = bytearray(struct.pack("<I", magic))
        head_data += bytearray(struct.pack("<H", checksum))
        head_data += bytearray(struct.pack("<H", head_type))
        head_data += bytearray(struct.pack("<H", data_len))
        head_data += bytearray(struct.pack("<H", version))
        head_data += bytearray(struct.pack("<I", fill_data))
        return head_data

    def init(self):
        self.serial = serial.Serial(
            self.port, self.baud, timeout=float(os.environ.get("SERIAL_TIMEOUT", 1))
        )

        # 初始化对话模式
        if self.conversation_mode == TypeCode.CIAS_SIGNLE_WAKEUP:
            byte_data = self.protocol_head_pack(
                MAGIC_DATA,
                CHECK_SUM,
                TypeCode.CIAS_SIGNLE_WAKEUP,
                0,
                0,
                FillCode.DEF_FILL,
            )
        elif self.conversation_mode == TypeCode.CIAS_CONTINUOUS_WAKEUP:
            byte_data = self.protocol_head_pack(
                MAGIC_DATA,
                CHECK_SUM,
                TypeCode.CIAS_CONTINUOUS_WAKEUP,
                0,
                0,
                FillCode.DEF_FILL,
            )
        else:
            byte_data = self.protocol_head_pack(
                MAGIC_DATA,
                CHECK_SUM,
                TypeCode.CIAS_PHYSICAL_WAKEUP,
                0,
                0,
                FillCode.DEF_FILL,
            )

        self.write(byte_data)

    def run_msg_handler(self):
        logger.success("Audio service started")
        for event in iter(self.device.audio_playlist_queue.get, None):
            logger.info("Audio download event: {0}".format(event["type"]))
            if event["type"] == "play_tts":
                # 发起播放开始事件
                self.update_fill_code(FillCode.TTS_FILL)
                logger.info("开始播放tts，先停止当前播放")
                self.write(self.stop_byte_data)
                # await asyncio.sleep(0.5)
                logger.info("停止播放")
                self.media_data = event["data"]
                self.write(self.start_byte_data)
                self.media_count = 0
                self.media_read_start = 0
                self.media_read_end = MEDIA_READ_LENGTH
                self.media(event["data"])

                self.audio_event_queue.put({"type": "on_play_begin", "data": ""})
            elif event["type"] == "play_mp3":
                if self.file_code != FillCode.MP3_FILL:
                    pass
                else:
                    self.update_fill_code(FillCode.MP3_FILL)
                    self.write(self.stop_byte_data)
                    self.write(self.start_byte_data)
                    self.media_data = event["data"]
                    self.media_count = 0
                    self.media_read_start = 0
                    self.media_read_end = MEDIA_READ_LENGTH
                    self.media(event["data"])
            elif event["type"] == "play_wait_words":
                logger.info("Play wait words, file_code: {0}".format(self.file_code))
                if self.file_code != FillCode.MP3_FILL:
                    pass
                else:
                    self.update_fill_code(FillCode.MP3_FILL)
                    self.write(self.stop_byte_data)
                    self.write(self.start_byte_data)
                    self.media_data = event["data"]
                    self.media_count = 0
                    self.media_read_start = 0
                    self.media_read_end = MEDIA_READ_LENGTH
                    self.media(event["data"])
                    logger.info("Play wait words end")

    def run_serial(self):
        logger.info("Serial service started")
        while True:
            try:
                data = self.serial.read(self.read_length)
                if len(data) < self.read_length:
                    continue

                self.data_parse(data)
                func = self.cmd_action.get(self.state)
                if func:
                    func(data)
                else:
                    # logger.debug(f'>>>>>>>>>>>>>>>>>>>>>{self.state}')
                    hex_string = ' '.join(format(x, '02X') for x in data)
                    logger.debug(f'->{hex_string}')
            except Exception as e:
                logger.error("Serial run error: {0}".format(e))

    def run(self):
        tasks = [
            threading.Thread(target=self.run_msg_handler),
            threading.Thread(target=self.run_serial),
        ]

        for task in tasks:
            task.start()

        for task in tasks:
            task.join()

            # if self.serial.in_waiting > 0:
            #     data = self.serial.read(self.read_length)
            #     if len(data) < self.read_length:
            #         continue

            #     self.data_parse(data)
            #     func = self.cmd_action.get(self.state)
            #     if func:
            #         func(data)
            #     else:
            #         # logger.debug(f'>>>>>>>>>>>>>>>>>>>>>{self.state}')
            #         hex_string = ' '.join(format(x, '02X') for x in data)
            #         logger.debug(f'->{hex_string}')

            # time.sleep(0.0001)

        self.serial.close()
        # await asyncio.sleep(0)

    def data_parse(self, data):
        read_length = len(data)
        if read_length >= STANDARD_HEAD_LEN:
            if self.read_length > STANDARD_HEAD_LEN:
                self.read_length = STANDARD_HEAD_LEN
            else:
                unpacked_data = struct.unpack(self.format_string, data)
                data_length = unpacked_data[DataHead.HEAD_LEN]

                # self.prev_state = self.state
                self.state = unpacked_data[DataHead.HEAD_TYPE]
                if data_length > 0:
                    self.read_length = data_length
        else:
            if self.read_length < STANDARD_HEAD_LEN:
                self.read_length = STANDARD_HEAD_LEN

    def upload(self, data):
        if not len(self.pcm_data):
            return

        logger.info("Pcm data to upload.")

        # self.device.audio_upload_queue.put(self.pcm_data)

        # with open('greatest_16k_s16le.mp3', 'rb') as file:
        #     self.media_data = file.read()
        #
        # print('media mp3 get')

        self.device.event_queue.put({"type": "on_record_end", "data": self.pcm_data})

        self.pcm_data = bytearray()
        self.file_code = FillCode.MP3_FILL

        # self.media_data = self.process_media_data
        #
        # self.update_fill_code(FillCode.MP3_FILL)
        # self.write(self.start_byte_data)
        # # self.media_state = MEDIA_MP3_CHECK
        # self.media_count = 0
        # self.media_read_start = 0
        # self.media_read_end = MEDIA_READ_LENGTH

    def send_media_data(self):
        send_data = self.media_data[self.media_read_start : self.media_read_end]
        if send_data:
            data_length = len(send_data)
            packed_data = bytearray(struct.pack("<H", data_length))
            self.head_byte_data[8:10] = packed_data
            send_data = self.head_byte_data + send_data
            self.write(send_data)
            self.media_count += 1
            self.media_read_start += MEDIA_READ_LENGTH
            self.media_read_end += MEDIA_READ_LENGTH
        else:
            self.write(self.end_byte_data)
            self.media_count = 0
            self.media_read_start = 0
            self.media_read_end = MEDIA_READ_LENGTH
            logger.info("Media data send completed")

            # 发起播放结束事件
            # self.event.on_next({"type": "on_play_end", "data": ""})
            # self.event_queue.put({"type": "on_play_end", "data": ""})

    def media(self, data):
        if self.media_count == 0:
            for i in range(10):
                self.send_media_data()
            return
        else:
            self.send_media_data()

    def media_end(self, data):
        if self.file_code == FillCode.MP3_FILL:
            if self.device.wait_words_voice_loop_play:
                self.update_fill_code(FillCode.MP3_FILL)
                self.write(self.start_byte_data)
                self.media_count = 0
                self.media_read_start = 0
                self.media_read_end = MEDIA_READ_LENGTH

    def wakeup(self, data):
        self.pcm_data = bytearray()
        self.audio_event_queue.put({"type": "wakeup", "data": data})

    def local(self, data):
        self.pcm_data = bytearray()
        self.device.audio_upload_cancel = True
        logger.info(f"LOCAL ASR NOTIFY")
        if len(data) == 2:
            data_int = struct.unpack("<h", data)[0]
            logger.info(f"LOCAL ASR NOTIFY: {data_int}")
            # 发起离线指令识别事件
            # self.event.on_next({"type": "on_recognition", "data": data_int})
            self.audio_event_queue.put({"type": "on_recognition", "data": data_int})

    def record(self, data):
        # 发起录音开始事件
        # 判断当前录音事件是否已经发起
        if self.lasted_event != "on_record_begin":
            # self.event.on_next({"type": "on_record_begin", "data": ""})
            self.audio_event_queue.put({"type": "on_record_begin", "data": ""})
            self.lasted_event = "on_record_begin"

        self.device.audio_upload_cancel = False
        if len(data) > STANDARD_HEAD_LEN:
            self.pcm_data += bytearray(data)

    def write(self, data):
        # hex_string = ' '.join(format(x, '02X') for x in data)
        # logger.debug(f'<-{hex_string}')
        self.serial.write(data)

    def stop(self):
        self.running = False

    def get_audio(self):
        return self.decode_data

    def set_conversation_mode(self, mode):
        if mode == "single":
            self.conversation_mode = TypeCode.CIAS_SIGNLE_WAKEUP
        elif mode == "manual":
            self.conversation_mode = TypeCode.CIAS_PHYSICAL_WAKEUP
        elif mode == "multi":
            self.conversation_mode = TypeCode.CIAS_CONTINUOUS_WAKEUP
        else:
            raise Exception("Unsupported conversation mode")
