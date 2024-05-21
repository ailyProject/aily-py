import os
import asyncio
import sys
import random
import threading
import time
from reactivex.subject import Subject
from loguru import logger
from queue import Queue
from dotenv import load_dotenv
from .hardwares.audio130x import AudioModule
from .db import Cache
from .llm import LLMs
from .tools import text_to_speech
import threading


class AIGC:
    # 事件
    wakeup = Subject()
    on_record_begin = Subject()
    on_record_end = Subject()
    on_play_begin = Subject()
    on_play_end = Subject()
    on_recognition = Subject()
    on_direction = Subject()
    on_invoke_start = Subject()
    on_invoke_end = Subject()

    audio_playlist_queue = Queue()
    llm_invoke_queue = Queue()
    event_queue = Queue()
    cache_queue = Queue()

    @staticmethod
    def load_config(env_file: str):
        if not load_dotenv(dotenv_path=env_file, override=True):
            raise RuntimeError("Failed to load the configuration file")
        logger.info("Configuration file loaded successfully")
        logger.info("model: {0}".format(os.getenv("LLM_MODEL")))

    def __init__(self, env_file: str):
        self.load_config(env_file)

        self.port = os.getenv("PORT")
        self.baudrate = os.getenv("BAUDRATE")

        self.hardware = None
        self.conversation_mode = os.getenv("CONVERSATION_MODE")

        self.audio_upload_cancel = False

        self.custom_llm_invoke = None
        self.llm = None
        self.llm_key = os.getenv("LLM_KEY")
        self.llm_model_name = os.getenv("LLM_MODEL") or "gpt-3.5-turbo"
        self.llm_server = os.getenv("LLM_URL")
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE") or 0.5)
        self.llm_pre_prompt = os.getenv("LLM_PRE_PROMPT")
        self.llm_max_token_length = int(os.getenv("LLM_MAX_TOKEN_LENGTH") or 16384)

        self.wait_words_list = []
        self.wait_words_voice_list = []
        self.wait_words_init = True
        self.wait_words_voice_auto_play = True
        self.wait_words_data = bytearray()
        self.wait_words_voice_loop_play = bool(os.getenv("WAIT_WORDS_LOOP_PLAY") or False)

        self.invalid_words = os.getenv("INVALID_WORDS")
        self.invalid_voice = None

        # 获取系统类型
        if sys.platform == "win32":
            self.root_path = "D://temp"
        else:
            self.root_path = "/tmp"

        self.wait_words_voice_path = self.root_path + "/wait_words_voice"

        # 最后对话时间
        self.last_conversation_time = 0
        # 聊天记录有效时间
        self.conversation_expired_at = 5 * 60

        # 数据库初始化
        if os.environ.get("DB_NAME"):
            db_path = os.path.abspath(os.environ.get("DB_NAME"))
        else:
            db_path = os.path.abspath("aigc.db")
        
        logger.debug("DB path: {0}".format(db_path))
        os.environ["DB_NAME"] = db_path

    def set_hardware(self, module):
        self.hardware = module

    def set_root_path(self, path):
        self.root_path = path

    def set_custom_llm_invoke(self, custom_invoke: callable):
        self.custom_llm_invoke = custom_invoke

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

    def set_wwords_loop_play(self, loop_play: bool):
        self.wait_words_voice_loop_play = loop_play

    def set_expired_time(self, expired_time: int):
        self.conversation_expired_at = expired_time

    def _hardware_init(self):
        if self.hardware is None:
            self.hardware = AudioModule(self)
        self.hardware.set_conversation_mode(self.conversation_mode)
        self.hardware.init()

    def _llm_init(self):
        self.llm = LLMs(self)
        if self.custom_llm_invoke:
            self.llm.set_custom_invoke(self.custom_llm_invoke)
    
    def _cache_init(self):
        self.cache = Cache(self)

    def _init(self):
        # 初始化等待词
        if self.wait_words_list:
            logger.info("Initializing wait words...")

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

            logger.info("Wait words initialization completed")

        # 读取默认
        if self.invalid_words:
            if os.path.exists(self.invalid_words):
                with open(self.invalid_words, "rb") as f:
                    self.invalid_voice = f.read()
            else:
                voice = text_to_speech(self.invalid_words)
                self.invalid_voice = voice

    def init(self):
        self._hardware_init()
        self._llm_init()
        self._cache_init()
        self._init()

    def set_conversation_mode(self, mode):
        self.conversation_mode = mode

    def play_wait_words(self, data):
        self.audio_playlist_queue.put({"type": "play_wait_words", "data": data})

    def play_invalid_words(self):
        if self.invalid_voice:
            self.audio_playlist_queue.put(
                {"type": "play_mp3", "data": self.invalid_voice}
            )
        else:
            logger.warning("Invalid words not set")

    def _auto_play_wait_words(self):
        if self.wait_words_voice_list:
            words_index = random.randint(0, len(self.wait_words_voice_list) - 1)
            self.play_wait_words(self.wait_words_voice_list[words_index])
            # with open(self.wait_words_voice_list[words_index], "rb") as f:
            #     data = f.read()
            # self.play_wait_words(data)
        else:
            logger.warning("Wait words not set")

    def send_message(self, content):
        if not content:
            self.play_invalid_words()
        else:
            # 聊天记录过期清理
            if time.time() - self.last_conversation_time > 60 * 60 * 24:
                self.llm.clear_chat_records()
                self.last_conversation_time = time.time()
            self.llm_invoke_queue.put({"type": "invoke", "data": content})

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
        self.audio_playlist_queue.put({"type": "play_tts", "data": data})

    def run_msg_handler(self):
        logger.success("AIGC service started")
        for event in iter(self.event_queue.get, None):
            logger.info("received event: {0}".format(event["type"]))
            if event["type"] == "wakeup":
                self.wakeup.on_next(event["data"])
            elif event["type"] == "on_record_begin":
                self.on_record_begin.on_next(event["data"])
            elif event["type"] == "on_record_end":
                # 播放等待音频
                if self.wait_words_voice_auto_play:
                    self._auto_play_wait_words()
                self.on_record_end.on_next(event["data"])
            elif event["type"] == "on_play_begin":
                self.on_play_begin.on_next(event["data"])
            elif event["type"] == "on_play_end":
                self.on_play_end.on_next(event["data"])
            elif event["type"] == "on_recognition":
                self.on_recognition.on_next(event["data"])
            elif event["type"] == "on_direction":
                self.on_direction.on_next(event["data"])
            elif event["type"] == "on_invoke_start":
                self.on_invoke_start.on_next(event["data"])
            elif event["type"] == "on_invoke_end":
                self.on_invoke_end.on_next(event["data"])
            else:
                pass
    
    async def main(self):
        self.init()
        tasks = [
            threading.Thread(target=self.run_msg_handler, daemon=True),
            threading.Thread(target=self.llm.run, daemon=True),
        ]
        self.hardware.start()
        self.cache.start()
        for task in tasks:
            task.start()

        self.hardware.join()
        self.cache.join()
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

    # async def main(self):
    #     self.init()
    #     tasks = [
    #         threading.Thread(target=self.run_msg_handler, daemon=True),
    #         self.hardware,
    #         self.llm,
    #         self.cache
    #     ]
    #     for task in tasks:
    #         task.start()

    #     for task in tasks:
    #         task.join()

    # def run(self):
    #     loop = asyncio.get_event_loop()
    #     try:
    #         loop.run_until_complete(self.main())
    #     except KeyboardInterrupt as e:
    #         pass
    #     finally:
    #         loop.close()
