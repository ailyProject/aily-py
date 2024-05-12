import unittest
# from dotenv import load_dotenv
from src.aily.tools import speech_to_text


class TextToSpeechTests(unittest.TestCase):
    def test_text_to_speech(self):
        with open("./output.wav", "rb") as f:
            voice = f.read()
        res = speech_to_text(voice)
        self.assertEquals(res, "Hello, this is a test")


if __name__ == "__main__":
    unittest.main()
