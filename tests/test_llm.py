import unittest
from agishell.llm import LLMs
from agishell.tools.speech_to_text import speech_to_text
from dotenv import load_dotenv

load_dotenv()


class TestLLM(unittest.TestCase):
    def test_completion(self):
        client = LLMs()
        res = client.send_message("解释下proxy的作用")
        print(res)

    def test_transcription(self):
        audio_file = open("./1706689005446.mp3", "rb")
        res = speech_to_text("./1706689005446.mp3", audio_file)
        print(res)

