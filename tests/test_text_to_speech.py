import unittest
from dotenv import load_dotenv
from src.aily.tools.text_to_speech import text_to_speech

load_dotenv(".env")


class TextToSpeechTests(unittest.TestCase):
    def test_text_to_speech(self):
        text = "Hello, this is a test"
        res = text_to_speech(text, output_file="./output.mp3")
        self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()
