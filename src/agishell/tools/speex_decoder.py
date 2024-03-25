import requests
from tenacity import retry, stop_after_attempt, wait_random_exponential
from loguru import logger


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=40))
def speex_decoder(file_content, result_type="mp3"):
    url = "http://101.34.93.13:7676/decode?resultType={0}".format(result_type)

    files = [
        ('file',
         ('speex_encode.pcm',
          file_content,
          'application/octet-stream'))
    ]

    try:
        response = requests.request("POST", url, files=files)
        if response.status_code != 200:
            raise RuntimeError("Failed to generate completion: {0}".format(response.text))

        return response.content
    except Exception as e:
        logger.error("Failed to request: {0}".format(e))
        raise e
