import requests


# TODO 看是否能本地实现

def speex_decoder(file_content, result_type="mp3"):
    url = "http://101.34.93.13:7676/decode?resultType={0}".format(result_type)

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
