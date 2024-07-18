"""
订阅获取对话内容（非阻塞方式）
"""

import json
from aily import Aily
from loguru import logger
from reactivex.scheduler import ThreadPoolScheduler
from reactivex import operators as ops
from aily.tools import speech_to_text, text_to_speech


def record_end_handler(pcm_data):
    # 语音转文字
    text = speech_to_text(pcm_data)
    logger.debug("转换后的文字为: {0}".format(text))
    # 调用LLM
    aily.send_message(text)


def invoke_end_handler(data):
    logger.debug("回答：{0}".format(data))
    # 文字转语音
    speech_data = text_to_speech(data)
    # 播放语音
    aily.play(speech_data)


def converstation_records_handler(data):
    # 将数据写入txt文件
    try:
        with open("./records.txt", "a") as f:
            f.write(json.dumps(data) + "\n")
    except Exception as e:
        logger.error("写入文件失败: {0}".format(e))


aily = Aily(".env")
aily.on_record_end.subscribe(lambda i: record_end_handler(i))
aily.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
# 异步订阅方式
aily.on_conversation_records.pipe(
    ops.observe_on(ThreadPoolScheduler(1))
).subscribe(lambda i: converstation_records_handler(i))

aily.run()
