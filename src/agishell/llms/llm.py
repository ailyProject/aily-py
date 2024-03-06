import asyncio
from reactivex.subject import Subject

from .openai import OpenAI


class ChatAI:
    event = Subject()

    # TODO Prompt Template
    # TODO Chat Cache
    # TODO Token数量限制
    # TODO 会话自动过期，过期时间配置
    # TODO 开始调用/结束调用事件发起

    def __init__(self, llm, event):
        if not llm:
            raise ValueError("请指定需要使用的服务, 如OpenAI, Gemini等")
        self.aigc_event = event
        self.llm = OpenAI()
        self.chat_records = []

        self.aigc_event.subscribe(lambda i: self.event_handler(i))

    def event_handler(self, event):
        if event["type"] == "wakeup":
            self.clear_chat_records()
        elif event["type"] == "invoke":
            asyncio.run(self.invoke(event["data"]))

    def set_key(self, key):
        self.llm.set_key(key)

    def set_model(self, model_name):
        self.llm.set_model(model_name)

    def set_server(self, url):
        self.llm.set_server(url)

    def set_temp(self, temperature):
        self.llm.set_temp(temperature)

    def set_pre_prompt(self, pre_prompt):
        if hasattr(self.llm, "set_pre_prompt"):
            self.llm.set_pre_prompt(pre_prompt)

    async def invoke(self, content):
        # 获取缓存聊天记录
        messages = self.chat_records
        messages.append({"role": "user", "content": content})

        # 开始调用事件发起
        self.event.on_next({"type": "invoke_start", "data": ""})
        invoke_result = await self.llm.invoke(messages)
        # TODO 根据返回值类型进行相应的操作，主要是对function call事件的处理
        self.chat_records.append({"role": invoke_result["role"], "content": invoke_result["content"]})
        # TODO token消耗统计等

        # 结束调用事件发起
        self.event.on_next({"type": "invoke_end", "data": invoke_result})

    def clear_chat_records(self):
        self.chat_records.clear()
