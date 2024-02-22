import asyncio
import struct
import time
import threading

from loguru import logger
from queue import SimpleQueue
from threading import Event


class AIGC(object):
    def __init__(self, port=None, baudrate: int = 1000000):
        self.port = port
        self.baud = baudrate
        self.audio = None
        # self.http_client = HttpClient()

        self.audio_upload_queue = SimpleQueue()
        self.audio_download_queue = SimpleQueue()

    def init(self, module):
        # self.audio = AudioModule(self)
        # self.audio.init()
        self.audio = module(self)
        self.audio.init()

    async def msg_handle(self):
        logger.info('msg_handle')
        while True:
            data = self.audio_upload_queue.get()

            if data:
                logger.info('audio upload')
                self.audio_download_queue.put(await self.http_client.audio_upload(data))
                # response = await self.http_client.audio_upload(data)
                # print(response)
                # print(type(response))
            await asyncio.sleep(0.1)

    async def main(self):
        self.init()
        # return
        tasks = [
            # threading.Thread(target=self.init, daemon=True),
            threading.Thread(target=asyncio.run, args=(self.msg_handle(),), daemon=True)
        ]

        self.audio.start()
        for task in tasks:
            task.start()

        self.audio.join()
        for task in tasks:
            task.join()

    def run(self):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main())
        except KeyboardInterrupt as e:
            # self.audio.stop()
            loop.stop()
        finally:
            loop.close()
        # self.init()
