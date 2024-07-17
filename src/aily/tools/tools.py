import time
import asyncio
import urllib.parse
from io import BytesIO
from loguru import logger
from ..models import STTBaiduOptions, STTAzureOptions, STTWhisperOptions, TTSAzureOptions, TTSOpenAIOptions, TTSBaiduOptions, TTSEdgeOptions


def pcm2wav(pcm_data):
    wav_data = [
        b"RIFF",
        (len(pcm_data) + 36).to_bytes(4, byteorder="little"),
        b"WAVE",
        b"fmt ",
        b"\x10\x00\x00\x00",
        b"\x01\x00\x01\x00",
        b"\x80\x3e\x00\x00",
        b"\x40\x1f\x00\x00",
        b"\x02\x00\x10\x00",
        b"data",
        len(pcm_data).to_bytes(4, byteorder="little"),
        pcm_data,
    ]

    # 组合wav文件内容
    wav_data = b"".join(wav_data)
    return wav_data


def stt_baidu(pcm_data, *, options: STTBaiduOptions) -> str:
    """
    https://cloud.baidu.com/doc/SPEECH/s/0lbxfnc9b

    pip install baidu-aip
    pip install chardet
    """
    from aip import AipSpeech

    start_time = int(time.time() * 1000)
    client = AipSpeech(options.app_id, options.key, options.secret_key)

    res = client.asr(
        pcm_data,
        "pcm",
        16000,
        {
            "dev_pid": options.dev_pid,
        },
    )

    logger.info("转换为文字耗时: {0}ms".format(int(time.time() * 1000) - start_time))

    return res["result"][0]


def stt_azure(pcm_data, *, options: STTAzureOptions) -> str:
    """
    pip install SpeechRecognition
    """

    import speech_recognition as sr

    wav_data = pcm2wav(pcm_data)

    start_time = int(time.time() * 1000)

    r = sr.Recognizer()

    audio_file = sr.AudioFile(BytesIO(wav_data))

    with audio_file as source:
        audio_data = r.record(source)

    try:
        res = r.recognize_azure(audio_data, options.key, options.lang, location=options.location)
        logger.info(
            "转换为文字耗时: {0}ms".format(int(time.time() * 1000) - start_time)
        )
        return res[0]
    except sr.UnknownValueError:
        logger.error("Azure Speech Recognition could not understand the audio")
    except sr.RequestError as e:
        logger.error(
            "Could not request results from Azure Speech Recognition service; {0}".format(
                e
            )
        )


def stt_whisper(pcm_data, *, options: STTWhisperOptions) -> str:
    """
    pip install openai
    """

    from openai import OpenAI

    wav_data = pcm2wav(pcm_data)
    start_time = int(time.time() * 1000)

    params = {"api_key": options.key}
    if options.url:
        params["base_url"] = options.url

    client = OpenAI(**params)

    res = client.audio.transcriptions.create(
        file=wav_data, model="whisper-1", response_format="text"
    )
    logger.info("转换为文字耗时: {0}ms".format(int(time.time() * 1000) - start_time))
    return res.text


def tts_baidu(text, *, options: TTSBaiduOptions) -> bytes:
    """
    https://cloud.baidu.com/doc/SPEECH/s/plbxhh4be

    pip install baidu-aip
    pip install chardet
    """

    from aip import AipSpeech

    start_time = int(time.time() * 1000)

    client = AipSpeech(options.app_id, options.key, options.secret_key)
    if not options.options:
        other = {"spd": 5, "vol": 15, "per": 4}
    else:
        other = options.options

    text = urllib.parse.quote(text)
    res = client.synthesis(text, options.lang, 1, other)
    if not isinstance(res, dict):
        logger.info(
            "转换为语音耗时: {0}ms".format(int(time.time() * 1000) - start_time)
        )
        return res
    else:
        if res["err_no"] == 513:
            audio_data = []
            for i in range(0, len(text), 60):
                temp_text = text[i : i + 60]
                # 对文本内容进行UrlEncode处理
                temp_text = urllib.parse.quote(temp_text)
                res = client.synthesis(temp_text, options.lang, 1, other)
                if not isinstance(res, dict):
                    audio_data.append(res)
                else:
                    logger.error(res)
                    break

            # 合并所有语音片段
            combined_audio = b"".join(audio_data)

            logger.info(
                "转换为语音耗时: {0}ms".format(int(time.time() * 1000) - start_time)
            )
            return combined_audio
        else:
            logger.error(res)


def tts_edge(text, *, options: TTSEdgeOptions) -> bytes:
    """
    pip install edge-tts
    """
    import edge_tts

    start_time = int(time.time() * 1000)

    async def get_audio():
        communicate = edge_tts.Communicate(text, options.voice)
        audio_strem = BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_strem.write(chunk["data"])

        audio_strem.seek(0)
        logger.info(
            "转换为语音耗时: {0}ms".format(int(time.time() * 1000) - start_time)
        )
        return audio_strem.read()

    return asyncio.run(get_audio())


def tts_openai(text, *, options: TTSOpenAIOptions) -> bytes:
    """
    pip install openai
    """

    from openai import OpenAI

    start_time = int(time.time() * 1000)

    params = {"api_key": options.key}
    if options.url:
        params["base_url"] = options.url
    client = OpenAI(**params)

    res = client.audio.speech.create(
        input=text, model="tts-1", voice=options.voice, response_format=options.response_format
    )

    logger.info("转换为语音耗时: {0}ms".format(int(time.time() * 1000) - start_time))
    return res.content


def tts_azure(text, *, options: TTSAzureOptions) -> bytes:
    """
    https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python
    pip install azure-cognitiveservices-speech
    """

    import azure.cognitiveservices.speech as speechsdk

    start_time = int(time.time() * 1000)
    speech_config = speechsdk.SpeechConfig(subscription=options.key, region=options.location)
    speech_config.speech_synthesis_voice_name = options.voice

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

    ssml_string = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{options.lang}'><voice name='{options.voice}'>{text}</voice></speak>"

    result = synthesizer.speak_ssml_async(ssml_string).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        logger.info(
            "转换为语音耗时: {0}ms".format(int(time.time() * 1000) - start_time)
        )
        return result.audio_data
    else:
        logger.error(result.reason)
