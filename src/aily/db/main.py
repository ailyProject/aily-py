import threading
from loguru import logger

from .crud import CRUDModel


class Cache(threading.Thread):
    def __init__(self, device):
        super(Cache, self).__init__()
        self.daemon = True
        self.cache_queue = device.cache_queue

    def run(self):
        self.crud = CRUDModel()
        self.crud.create_default_table()
        while True:
            event = self.cache_queue.get()
            if not event:
                continue

            if event["type"] == "conversations":
                try:
                    self.crud.insert(
                        "conversations", ["created_at", "role", "msg"], event["data"]
                    )
                except Exception as e:
                    logger.error(f"Cache insert error: {e}")
