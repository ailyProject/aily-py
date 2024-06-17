import os
import sys
import random
import threading
import time
from reactivex.subject import Subject
from loguru import logger
from dotenv import load_dotenv
from .db import AilyCache
from .llm import AilyLLM
from .hardwares import AilyAudio, AilyTTS
from .tools import text_to_speech

from reactivex.scheduler import ThreadPoolScheduler
from reactivex import operators as ops


class Aily:
    # 事件
    wakeup = Subject()
    on_function_call = Subject()
    on_custom_invoke = Subject()
    on_custom_invoke_vision = Subject()
    on_record_begin = Subject()
    on_record_end = Subject()
    on_play_begin = Subject()
    on_play_end = Subject()
    on_recognition = Subject()
    on_direction = Subject()
    on_invoke_start = Subject()
    on_invoke_end = Subject()
    on_invalid_msg = Subject()

    on_error = Subject()

    aily_event = Subject()

    @staticmethod
    def load_config(env_file: str):
        if not load_dotenv(dotenv_path=env_file, override=True):
            logger.warning("No .env file found")
        else:
            logger.success("Load .env file successfully")

    def __init__(self, env_file: str):
        self.load_config(env_file)

        self.port = os.getenv("PORT") or None
        self.baudrate = os.getenv("BAUDRATE")
        self.timeout = os.getenv("SERIAL_TIMEOUT") or 1

        self.audio = None
        self.conversation_mode = os.getenv("CONVERSATION_MODE") or "single"

        # aily tts
        self.aily_tts = None
        self._use_aily_tts = os.getenv("USE_AILY_TTS") or False
        self._tts_port = os.getenv("TTS_PORT") or None
        self._tts_baudrate = os.getenv("TTS_BAUDRATE") or 115200

        # self.custom_llm_invoke = False
        self._custom_invoke = False
        self._custom_invoke_vision = False

        self.llm = None
        self.llm_key = os.getenv("LLM_KEY") or None
        self.llm_model_name = os.getenv("LLM_MODEL") or "gpt-3.5-turbo"
        self.llm_server = os.getenv("LLM_URL") or None
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE") or 0.5)
        self.llm_pre_prompt = os.getenv("LLM_PRE_PROMPT")
        self.llm_max_token_length = int(os.getenv("LLM_MAX_TOKEN_LENGTH") or 1200)

        self.llm_vision_model_name = os.getenv("LLM_VISION_MODEL") or self.llm_model_name
        self.llm_vision_key = os.getenv("LLM_VISION_KEY") or self.llm_key
        self.llm_vision_server = os.getenv("LLM_VISION_URL") or self.llm_server

        self.llm_tools = None
        self.llm_tool_choice = None

        self.wait_words_list = []
        self.wait_words_voice_list = []
        self.wait_words_init = True
        self.wait_words_voice_auto_play = True
        self.wait_words_data = bytearray()
        self.wait_words_voice_loop_play = bool(
            os.getenv("WAIT_WORDS_LOOP_PLAY") or False
        )

        self.invalid_words = os.getenv("INVALID_WORDS") or None
        self.invalid_voice = None

        if self.llm_key is None:
            raise RuntimeError("LLM_KEY is not set")
        if self.llm_server is None:
            raise RuntimeError("LLM_URL is not set")

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

    @property
    def use_aily_tts(self):
        return self._use_aily_tts

    @use_aily_tts.setter
    def use_aily_tts(self, value):
        self._use_aily_tts = value

    @property
    def tts_port(self):
        return self._tts_port

    @tts_port.setter
    def tts_port(self, value):
        self._tts_port = value

    @property
    def tts_baudrate(self):
        return self._tts_baudrate

    @tts_baudrate.setter
    def tts_baudrate(self, value):
        self._tts_baudrate = value

    @property
    def custom_invoke(self):
        return self._custom_invoke

    @custom_invoke.setter
    def custom_invoke(self, value):
        self._custom_invoke = value

    @property
    def custom_invoke_vision(self):
        return self._custom_invoke_vision

    @custom_invoke_vision.setter
    def custom_invoke_vision(self, value):
        self._custom_invoke_vision = value

    def set_root_path(self, path):
        self.root_path = path

    def register_tools(self, tools):
        self.llm_tools = tools

    def choice_tool(self, tool_name):
        self.llm_tool_choice = tool_name

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

    def set_conversation_mode(self, mode):
        self.conversation_mode = mode

    def play_wait_words(self, data):
        # self.audio_playlist_queue.put({"type": "play_wait_words", "data": data})
        self.aily_event.on_next({"type": "play_mp3", "data": data})

    # def play_invalid_words(self):
    #     if self.invalid_voice:
    #         self.aily_event.on_next({"type": "play_mp3", "data": self.invalid_voice})
    #     else:
    #         logger.warning("Invalid words not set")

    def _auto_play_wait_words(self):
        if self.wait_words_voice_list:
            words_index = random.randint(0, len(self.wait_words_voice_list) - 1)
            self.play_wait_words(self.wait_words_voice_list[words_index])
            time.sleep(1)
            # with open(self.wait_words_voice_list[words_index], "rb") as f:
            #     data = f.read()
            # self.play_wait_words(data)
        else:
            logger.warning("Wait words not set")

    def send_message(self, content):
        if not content:
            # self.play_invalid_words()
            self.on_invalid_msg.on_next({"data": ""})
        else:
            # 聊天记录过期清理
            if time.time() - self.last_conversation_time > 60 * 60 * 24:
                self.llm.clear_chat_records()
                self.last_conversation_time = time.time()
            # self.llm_invoke_queue.put({"type": "invoke", "data": content})
            self.aily_event.on_next({"type": "invoke", "data": content})

    def reply_message(self, call_id, content, reply_type="text"):
        if not content:
            return

        self.aily_event.on_next(
            {"type": "reply", "data": {"call_id": call_id, "content": content, "reply_type": reply_type}})

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
        # self.audio_playlist_queue.put({"type": "play_tts", "data": data})
        if self.use_aily_tts:
            self.aily_event.on_next({"type": "play_tts_by_aily", "data": data})
        else:
            self.aily_event.on_next({"type": "play_tts", "data": data})

    def event_handler(self, event):
        event_type = event["type"]
        logger.debug("Event: {0}".format(event_type))

        if event_type == "wakeup":
            self.wakeup.on_next(event["data"])
        elif event_type == "on_record_begin":
            self.on_record_begin.on_next(event["data"])
        elif event_type == "on_record_end":
            # 播放等待音频
            if self.wait_words_voice_auto_play:
                self._auto_play_wait_words()
            self.on_record_end.on_next(event["data"])
        elif event_type == "on_play_begin":
            self.on_play_begin.on_next(event["data"])
        elif event_type == "on_play_end":
            if self.conversation_mode != "multi":
                self.aily_event.on_next({"type": "clear"})
            self.on_play_end.on_next(event["data"])
        elif event_type == "on_recognition":
            self.on_recognition.on_next(event["data"])
        elif event_type == "on_direction":
            self.on_direction.on_next(event["data"])
        elif event_type == "on_invoke_start":
            self.on_invoke_start.on_next(event["data"])
        elif event_type == "on_invoke_end":
            self.on_invoke_end.on_next(event["data"])
        elif event_type == "on_function_call":
            self.on_function_call.on_next(event["data"])
        elif event_type == "on_custom_invoke":
            self.on_custom_invoke.on_next(event["data"])
        elif event_type == "on_custom_invoke_vision":
            self.on_custom_invoke_vision.on_next(event["data"])
        else:
            pass

    def _init_audio(self):
        if self.audio is None:
            self.audio = AilyAudio()

        self.audio.port = self.port
        self.audio.baudrate = self.baudrate
        self.audio.timeout = self.timeout
        self.audio.event = self.aily_event
        self.audio.loop_play_wait_words = self.wait_words_voice_loop_play
        self.audio.set_mode(self.conversation_mode)
        self.audio.init()
        logger.info("Hardware initialization completed")

    def _init_tts(self):
        if self.aily_tts is None:
            self.aily_tts = AilyTTS()

        self.aily_tts.port = self.tts_port
        self.aily_tts.baudrate = self.tts_baudrate
        self.aily_tts.event = self.aily_event
        self.aily_tts.init()
        logger.info("TTS initialization completed")

    def _init_llm(self):
        self.llm = AilyLLM()
        self.llm.key = self.llm_key
        self.llm.url = self.llm_server
        self.llm.temperature = self.llm_temperature
        self.llm.max_token_length = self.llm_max_token_length
        self.llm.pre_prompt = self.llm_pre_prompt
        self.llm.model = self.llm_model_name
        self.llm.vision_key = self.llm_vision_key
        self.llm.vision_url = self.llm_vision_server
        self.llm.vision_model = self.llm_vision_model_name

        self.llm.custom_invoke = self.custom_invoke
        self.llm.custom_invoke_vision = self.custom_invoke_vision
        self.llm.tools = self.llm_tools
        self.llm.tool_choice = self.llm_tool_choice

        self.llm.event = self.aily_event

        logger.info("LLM initialization completed")

    def _init_cache(self):
        self.cache = AilyCache()
        self.cache.event = self.aily_event
        logger.info("Cache initialization completed")

    def _init_wait_words(self):
        for words in self.wait_words_list:
            # 判断是纯文本还是语音文件地址
            if os.path.exists(words):
                # self.wait_words_voice_list.append(words)
                with open(words, "rb") as f:
                    data = f.read()
                    self.wait_words_voice_list.append(data)
            else:
                # 将文字转为语音
                try:
                    speech_data = text_to_speech(words)
                    self.wait_words_voice_list.append(speech_data)
                except Exception as e:
                    logger.error("Text to speech failed: {0}".format(e))
                # filename = str(int(time.time() * 1000)) + ".mp3"
                # save_path = self.wait_words_voice_path + "/" + filename
                # with open(save_path, "wb") as f:
                #     f.write(speech_data)
                # self.wait_words_voice_list.append(save_path)

        logger.info("Wait words initialization completed")

    def _init_invalid_words(self):
        if self.invalid_words:
            if os.path.exists(self.invalid_words):
                with open(self.invalid_words, "rb") as f:
                    self.invalid_voice = f.read()
            else:
                voice = text_to_speech(self.invalid_words)
                self.invalid_voice = voice
        logger.info("Invalid words initialization completed")

    def init(self):
        self._init_audio()
        self._init_llm()
        self._init_cache()
        self._init_wait_words()
        self._init_invalid_words()

        if self.use_aily_tts:
            self._init_tts()

        # 订阅
        self.aily_event.pipe(
            ops.observe_on(ThreadPoolScheduler(1))
        ).subscribe(self.event_handler)

        logger.success("All initialization completed~~~")

    def run(self):
        try:
            self.init()
            tasks = [
                threading.Thread(target=self.audio.start, daemon=True),
                threading.Thread(target=self.llm.start, daemon=True),
                threading.Thread(target=self.cache.start, daemon=True),
            ]

            if self.use_aily_tts:
                tasks.append(threading.Thread(target=self.aily_tts.start, daemon=True))

            for task in tasks:
                task.start()

            for task in tasks:
                task.join()
        except KeyboardInterrupt as e:
            pass
        finally:
            logger.warning("Aily shutdown~~~")
