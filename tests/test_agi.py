import sys
import unittest
from agishell.llms.openai import ChatOpenAI


class TestAgiLLM(unittest.IsolatedAsyncioTestCase):
    async def test_openai_invoke(self):
        chat_openai = ChatOpenAI()
        chat_openai.set_key("")
        chat_openai.set_server("")
        result = await chat_openai.invoke([{"role": "user", "content": "天空为什么是蓝色的"}])
        print(result)

        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
