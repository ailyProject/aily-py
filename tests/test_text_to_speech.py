import unittest
from dotenv import load_dotenv
from src.aily.tools.text_to_speech import text_to_speech


class TextToSpeechTests(unittest.TestCase):
    def test_text_to_speech(self):
        load_dotenv()
        text = "Hello, this is a test"
        res = text_to_speech(text)
        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()
