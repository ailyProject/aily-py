import asyncio
from reactivex.subject import Subject
from hardwares.audio130x import AudioModule
from llms.llm import ChatAI
from dotenv import load_dotenv

load_dotenv()


class AIGC:
    event = Subject()
    _hardware_event = Subject()
    _llm_event = Subject()

    def __init__(self, port=None, baudrate: int = 1000000):
        self.port = port
        self.baudrate = baudrate

        self.hardware = None
        self.llm_model = "openai"
        self.llm = None

    def set_hardware(self, module):
        self.hardware = module

    def set_llm(self, llm_model):
        # TODO 判断llm是否在支持的列表中
        self.llm_model = llm_model

    def init(self):
        if self.hardware is None:
            self.hardware = AudioModule(self.port, self.baudrate, self._hardware_event)
        self.hardware.init()
        self.hardware.event.subscribe(lambda i: self.hardware_event_handler(i))
        self.llm = ChatAI(self.llm_model, self._llm_event)
        self.llm.event.subscribe(lambda i: self.llm_event_handler(i))

    def hardware_event_handler(self, event):
        if event["type"] == "wakeup":
            # 监测到是唤醒，则向大模型发起唤醒事件，清空聊天记录
            self._llm_event.on_next({"type": "wakeup", "data": ""})

        self.event.on_next(event)

    def llm_event_handler(self, event):
        self.event.on_next(event)

    def send_message(self, content):
        self._llm_event.on_next({"type": "invoke", "data": content})

    def set_key(self, key):
        self.llm.set_key(key)

    def set_model(self, model_name):
        self.llm.set_model(model_name)

    def set_server(self, url):
        self.llm.set_server(url)

    def set_temp(self, temperature):
        self.llm.set_temp(temperature)

    def set_pre_prompt(self, pre_prompt):
        self.llm.set_pre_prompt(pre_prompt)

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
