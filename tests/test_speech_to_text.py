import unittest
from dotenv import load_dotenv
from src.aily.tools import speech_to_text


class TextToSpeechTests(unittest.TestCase):
    def test_text_to_speech(self):
        load_dotenv()
        with open("./output.mp3", "rb") as f:
            voice = f.read()
        res = speech_to_text(voice, "output.mp3")
        self.assertEquals(res, "Hello, this is a test")


if __name__ == "__main__":
    unittest.main()
