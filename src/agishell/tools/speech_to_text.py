import os
import requests

from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(5))
def speech_to_text(filename, file, base_url=None, api_key=None):
    url = "{0}/audio/transcriptions".format(base_url if base_url else os.getenv("OPENAI_URL"))
    files = {
        'file': (filename, file),
    }
    req_data = {
        "model": "whisper-1",
    }

    headers = {
        'Authorization': 'Bearer {0}'.format(api_key if api_key else os.getenv("OPENAI_KEY")),
    }

    res = requests.post(url, data=req_data, files=files, headers=headers)
    if res.status_code != 200:
        raise Exception("Failed to convert speech to text: {0}".format(res.text))
    return res.text
