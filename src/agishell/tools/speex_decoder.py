import requests


def speex_decoder(file_content):
    url = "http://101.34.93.13:7676/decode"

    files = [
        ('file',
         ('speex_encode.pcm',
          file_content,
          'application/octet-stream'))
    ]

    response = requests.request("POST", url, files=files)
    if response.status_code != 200:
        raise RuntimeError("Failed to generate completion: {0}".format(response.text))

    return response.content
