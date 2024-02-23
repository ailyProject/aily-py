import requests


def text_to_speech(text):
    url = "http://101.34.93.13:7676/tts"
    data = {
        "content": text
    }

    response = requests.request("POST", url, json=data)
    if response.status_code != 200:
        raise RuntimeError("Failed to request: {0}".format(response.text))

    return response.content
