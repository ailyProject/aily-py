from reactivex.subject import Subject


class AGIShellLLM:
    result = Subject()

    # TODO Prompt Template
    # TODO Chat Cache
    # TODO Token数量限制
    # TODO 会话自动过期，过期时间配置

    def __init__(self, llm):
        self.llm = llm
        self.chat_records = []

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

        invoke_result = await self.llm.invoke(messages)
        # TODO 根据返回值类型进行相应的操作
        self.chat_records.append({"role": invoke_result["role"], "content": invoke_result["content"]})
        # TODO token消耗统计等

        self.result.on_next(invoke_result)

        return invoke_result

    async def clear(self):
        self.chat_records.clear()
