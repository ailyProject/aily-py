import asyncio
from reactivex.subject import Subject
from .hardwares.audio130x import AudioModule
from .llm import LLMs


class AIGC:
    event = Subject()
    _input_hardware_event = Subject()
    _input_llm_event = Subject()

    def __init__(self, port=None, baudrate: int = 1000000):
        self.port = port
        self.baudrate = baudrate

        self.hardware = None

        self.llm = None
        self.llm_key = ""
        self.llm_model_name = ""
        self.llm_server = ""
        self.llm_temperature = 0.5
        self.llm_pre_prompt = ""

    def set_hardware(self, module):
        self.hardware = module

    def init(self):
        if self.hardware is None:
            self.hardware = AudioModule(self.port, self.baudrate, self._input_hardware_event)
        self.hardware.init()
        self.hardware.event.subscribe(lambda i: self.hardware_event_handler(i))
        if self.llm is None:
            self.llm = LLMs(self._input_llm_event)
            self.llm.set_key(self.llm_key)
            self.llm.set_model(self.llm_model_name)
            self.llm.set_server(self.llm_server)
            self.llm.set_temp(self.llm_temperature)
            self.llm.set_pre_prompt(self.llm_pre_prompt)
        self.llm.event.subscribe(lambda i: self.llm_event_handler(i))

    def hardware_event_handler(self, event):
        if event["type"] == "wakeup":
            # 监测到是唤醒，则向大模型发起唤醒事件，清空聊天记录
            self._input_llm_event.on_next({"type": "wakeup", "data": ""})

        self.event.on_next(event)

    def llm_event_handler(self, event):
        self.event.on_next(event)

    def send_message(self, content):
        self._input_llm_event.on_next({"type": "invoke", "data": content})

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
