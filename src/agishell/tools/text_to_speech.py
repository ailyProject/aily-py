import requests


def text_to_speech(text, voice="zh-CN-XiaoxiaoNeural"):
    url = "http://101.34.93.13:7979/tts"
    data = {
        "content": text,
        "voice": voice
    }

    response = requests.request("POST", url, json=data)
    if response.status_code != 200:
        raise RuntimeError("Failed to request: {0}".format(response.text))

    return response.content
