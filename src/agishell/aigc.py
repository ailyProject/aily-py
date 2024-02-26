import asyncio
from reactivex.subject import Subject


class AIGC:
    hardware_data = Subject()
    llm_invoke_start = Subject()
    llm_invoke_end = Subject()
    llm_invoke_result = Subject()
    

    def __init__(self, module, llm):
        self.hardware = module
        self.llm = llm
        self.hardware.received_data.subscribe(
            lambda i: self.hardware_data.on_next(i))
        self.llm.event.subscribe(lambda i: self.llm_event_handler(i))

    def init(self):
        self.hardware.init()
    
    def llm_event_handler(self, event):
        if event == "invoke_start":
            self.llm_invoke_start.on_next()
        elif event == "invoke_end":
            self.llm_invoke_end.on_next()
        elif event == "invoke_result":
            self.llm_invoke_result.on_next()

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
