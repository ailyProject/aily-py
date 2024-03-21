import os
import asyncio
import sys
import random
import threading
import time
from reactivex.subject import Subject
from loguru import logger
from queue import SimpleQueue
from .hardwares.audio130x import AudioModule
from .llm import LLMs
from .tools import text_to_speech


class AIGC:
    event = Subject()
    _input_hardware_event = Subject()
    _input_llm_event = Subject()

    def __init__(self, port=None, baudrate: int = 1000000, llm=None):
        self.port = port
        self.baudrate = baudrate

        self.hardware = None
        self.conversation_mode = "multi"

        self.audio_upload_queue = SimpleQueue()
        self.audio_download_queue = SimpleQueue()
        self.audio_event_queue = SimpleQueue()

        self.audio_upload_cancel = False

        self.custom_llm = llm
        self.custom_llm_invoke = None
        self.llm = None
        self.llm_key = ""
        self.llm_model_name = ""
        self.llm_server = ""
        self.llm_temperature = 0.5
        self.llm_pre_prompt = ""
        self.llm_max_token_length = 16384

        self.wait_words_list = []
        self.wait_words_voice_list = []
        self.wait_words_init = True
        self.wait_words_voice_auto_play = True
        self.wait_words_data = bytearray()

        # 获取系统类型
        if sys.platform == "win32":
            self.root_path = "D://temp"
        else:
            self.root_path = "/tmp"

        self.wait_words_voice_path = self.root_path + "/wait_words_voice"

    def set_hardware(self, module):
        self.hardware = module

    def set_root_path(self, path):
        self.root_path = path

    def set_custom_llm_invoke(self, custom_invoke: callable):
        self.custom_llm_invoke = custom_invoke

    def set_custom_llm(self, module):
        self.custom_llm = module

    def clear_wait_words(self):
        self.wait_words_list.clear()

        if not os.path.exists(self.wait_words_voice_path):
            return

        for file in os.listdir(self.wait_words_voice_path):
            os.remove(self.wait_words_voice_path + "/" + file)

    def set_wait_words(self, words):
        if self.wait_words_init:
            self.wait_words_init = False
            self.clear_wait_words()

        self.wait_words_list.append(words)

    def set_wwords_auto_play(self, auto_play: bool):
        self.wait_words_voice_auto_play = auto_play

    def init(self):
        if self.hardware is None:
            self.hardware = AudioModule(self)
        self.hardware.set_conversation_mode(self.conversation_mode)
        self.hardware.init()
        # self.hardware.event.subscribe(lambda i: self.hardware_event_handler(i))

        if self.custom_llm is None:
            self.llm = LLMs(self)
            if self.custom_llm_invoke:
                self.llm.set_custom_invoke(self.custom_llm_invoke)
        else:
            self.llm = self.custom_llm(self._input_llm_event)

        # 初始化等待词
        if self.wait_words_list:
            logger.info("初始化等待词...")

            for words in self.wait_words_list:
                # 判断是纯文本还是语音文件地址
                if os.path.exists(words):
                    # self.wait_words_voice_list.append(words)
                    with open(words, "rb") as f:
                        data = f.read()
                        self.wait_words_voice_list.append(data)
                else:
                    # 将文字转为语音
                    speech_data = text_to_speech(words)
                    self.wait_words_voice_list.append(speech_data)
                    # filename = str(int(time.time() * 1000)) + ".mp3"
                    # save_path = self.wait_words_voice_path + "/" + filename
                    # with open(save_path, "wb") as f:
                    #     f.write(speech_data)
                    # self.wait_words_voice_list.append(save_path)

            logger.info("初始化等待词完成")

    def hardware_event_handler(self, event):
        if event["type"] == "on_record_end":
            if self.wait_words_voice_auto_play:
                logger.info('on_record_end.')
                self._auto_play_wait_words()
        self.event.on_next(event)

    def llm_event_handler(self, event):
        self.event.on_next(event)

    def msg_handler(self):
        while True:
            data = self.audio_event_queue.get()
            if self.audio_upload_cancel:
                logger.info("取消上传")
            else:
                self.hardware_event_handler(data)

    def set_conversation_mode(self, mode):
        self.conversation_mode = mode

    def play_wait_words(self, data):
        # self._input_hardware_event.on_next({"type": "play_wait_words", "data": data})
        self.audio_download_queue.put({"type": "play_wait_words", "data": data})

    def _auto_play_wait_words(self):
        if self.wait_words_voice_list:
            words_index = random.randint(0, len(self.wait_words_voice_list) - 1)
            self.play_wait_words(self.wait_words_voice_list[words_index])
            # with open(self.wait_words_voice_list[words_index], "rb") as f:
            #     data = f.read()
            # self.play_wait_words(data)
        else:
            logger.warning("未设置等待词")

    def send_message(self, content):
        # self._input_llm_event.on_next({"type": "send_message", "data": content})
        self.llm._send_message(content)

    def set_key(self, key):
        if self.llm:
            self.llm.set_key(key)
        self.llm_key = key

    def set_model(self, model_name):
        if self.llm:
            self.llm.set_model(model_name)
        self.llm_model_name = model_name

    def set_server(self, url):
        if self.llm:
            self.llm.set_server(url)
        self.llm_server = url

    def set_temp(self, temperature):
        if self.llm:
            self.llm.set_temp(temperature)
        self.llm_temperature = temperature

    def set_pre_prompt(self, pre_prompt):
        if self.llm:
            self.llm.set_pre_prompt(pre_prompt)
        self.llm_pre_prompt = pre_prompt

    def play(self, data):
        # self._input_hardware_event.on_next({"type": "play", "data": data})
        self.audio_download_queue.put({"type": "play", "data": data})

    async def main(self):
        self.init()
        tasks = [
            threading.Thread(target=self.msg_handler, daemon=True),
        ]
        self.hardware.start()
        for task in tasks:
            task.start()

        self.hardware.join()
        for task in tasks:
            task.join()

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main())
        except KeyboardInterrupt as e:
            pass
        finally:
            loop.close()
