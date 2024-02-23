import os
import unittest
from dotenv import load_dotenv
from agishell.llms.openai import ChatOpenAI
from agishell import AGIShellLLM

load_dotenv(".env")


class TestAgiLLM(unittest.IsolatedAsyncioTestCase):
    async def test_openai_invoke(self):
        chat_openai = ChatOpenAI()
        chat_openai.set_key(os.getenv("OPENAI_KEY"))
        chat_openai.set_server(os.getenv("OPENAI_PROXY_URL"))
        result = await chat_openai.invoke([{"role": "user", "content": "天空为什么是蓝色的"}])
        print(result)

        self.assertIsNotNone(result)

    async def test_agi_invoke(self):
        llm = AGIShellLLM(ChatOpenAI())
        llm.set_key(os.getenv("OPENAI_KEY"))
        llm.set_server(os.getenv("OPENAI_PROXY_URL"))
        result = await llm.invoke("天空为什么是蓝色的")

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
