from reactivex.subject import Subject


class AGIShellLLM:
    result = Subject()

    # TODO Prompt Template
    # TODO Chat Cache
    # TODO Token数量限制

    def __init__(self, llm):
        self.llm = llm
        self.chat_records = []

    async def invoke(self, content):
        # 获取缓存聊天记录
        messages = self.chat_records
        messages.append({"role": "user", "content": content})

        result = await self.llm.invoke(content)
        # TODO 根据返回值类型进行相应的操作
        self.chat_records.append({"role": result["role"], "content": result["content"]})
        # TODO token消耗统计等

        self.result.on_next(result)

    async def clear(self):
        self.chat_records.clear()
