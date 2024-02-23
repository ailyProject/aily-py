import asyncio
from reactivex.subject import Subject


class AIGC:
    hardware_data = Subject()

    def __init__(self, module):
        self.hardware = module
        self.hardware.received_data.subscribe(
            lambda i: self.hardware_data.on_next(i))

    def init(self):
        self.hardware.init()

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
