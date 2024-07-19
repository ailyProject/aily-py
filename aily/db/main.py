import time
import json
import urllib.parse

from loguru import logger
from .crud import CRUDModel
from reactivex.scheduler import ThreadPoolScheduler
from reactivex import operators as ops


class AilyCache:
    def __init__(self):
        self._event = None

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, value):
        self._event = value

    def event_handler(self, event):
        event_type = event["type"]
        # logger.debug(f"Cache Event handler: {event_type}")
        if event_type == "conversations":
            try:
                content = urllib.parse.quote(event["data"]["content"])
                crud = CRUDModel()
                crud.create_default_table()
                role = event["data"]["role"]
                msg_type = event["data"]["msg_type"]
                msg = json.dumps(content) if isinstance(content, dict) else content
                cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                crud.insert(
                    "conversations", ["created_at", "role", "msg_type", "msg"], [cur_time, role, msg_type, msg]
                )
            except Exception as e:
                logger.error(f"Cache insert error: {e}")

    def start(self):
        self._event.pipe(
            ops.observe_on(ThreadPoolScheduler(1))
        ).subscribe(self.event_handler)
