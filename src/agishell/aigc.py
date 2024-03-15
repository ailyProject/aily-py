import os
import asyncio
from reactivex.subject import Subject
from .hardwares.audio130x import AudioModule
from .llm import LLMs


class AIGC:
    event = Subject()
    _input_hardware_event = Subject()
    _input_llm_event = Subject()

    def __init__(self, port=None, baudrate: int = 1000000, llm=None):
        self.port = port
        self.baudrate = baudrate

        self.hardware = None
        self.conversation_mode = "multi"

        self.custom_llm = llm
        self.custom_llm_invoke = None
        self.llm = None
        self.llm_key = ""
        self.llm_model_name = ""
        self.llm_server = ""
        self.llm_temperature = 0.5
        self.llm_pre_prompt = ""
        self.llm_max_token_length = 16384

    def set_hardware(self, module):
        self.hardware = module

    def set_custom_llm_invoke(self, custom_invoke: callable):
        self.custom_llm_invoke = custom_invoke

    def set_custom_llm(self, module):
        self.custom_llm = module

    def init(self):
        if self.hardware is None:
            self.hardware = AudioModule(self.port, self.baudrate, self._input_hardware_event)
        self.hardware.set_conversation_mode(self.conversation_mode)
        self.hardware.init()
        self.hardware.event.subscribe(lambda i: self.hardware_event_handler(i))

        if self.custom_llm is None:
            self.llm = LLMs(
                self._input_llm_event,
                self.llm_server if self.llm_server else os.getenv("LLM_URL"),
                self.llm_key if self.llm_key else os.getenv("LLM_KEY"),
                self.llm_model_name if self.llm_model_name else "gpt-3.5-turbo",
                self.llm_pre_prompt if self.llm_pre_prompt else os.getenv("LLM_PRE_PROMPT"),
                self.llm_temperature if self.llm_temperature else 0.5,
                self.llm_max_token_length if self.llm_max_token_length else 16384
            )
            if self.custom_llm_invoke:
                self.llm.set_custom_invoke(self.custom_llm_invoke)
        else:
            self.llm = self.custom_llm(self._input_llm_event)

        self.llm.event.subscribe(lambda i: self.llm_event_handler(i))

    def hardware_event_handler(self, event):
        self.event.on_next(event)

    def llm_event_handler(self, event):
        self.event.on_next(event)

    def set_conversation_mode(self, mode):
        self.conversation_mode = mode

    def send_message(self, content):
        self._input_llm_event.on_next({"type": "send_message", "data": content})
        # self.llm.send_message(content)

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
        self._input_hardware_event.on_next({"type": "play", "data": data})

    async def main(self):
        await asyncio.gather(self.hardware.run())

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main())
        except KeyboardInterrupt as e:
            pass
        finally:
            loop.close()
