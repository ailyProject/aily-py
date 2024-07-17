"""
function calls example
"""

import base64
import subprocess

from aily import Aily
from aily.tools import speech_to_text, text_to_speech
from loguru import logger


def call_camera(output_path):
    subprocess.run(["rpicam-jpeg", "--output", output_path, "--timeout", "2000", "--width", "640", "--height", "480"])


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def function_call_handler(event):
    logger.info("收到函数调用请求：{0}".format(event))
    call_id = event["id"]
    if event["name"] == "get_picture":
        logger.debug("调用摄像头拍照")
        call_camera("./sample.jpg")

        # 方式一：直接返回图片的URL
        # content = 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg'

        # 方式二：返回图片的base64编码
        image = encode_image("./sample.jpg")
        content = f"data:image/jpeg;base64,{image}"
        logger.debug("content: {0}".format(content))
        aigc.reply_message(call_id, content, "image")


def record_end_handler(pcm_data):
    text = speech_to_text(pcm_data)
    logger.info("转换后的文字为: {0}".format(text))
    aigc.send_message(text)


def invoke_end_handler(data):
    logger.info("回答：{0}".format(data))
    speech_data = text_to_speech(data)
    aigc.play(speech_data)


tools = [{
    "type": "function",
    "function": {
        "name": "get_picture",
        "description": "此函数用于调用摄像头拍照，获取周围环境的照片，是aily的眼睛，提供视觉能力输入",
        "parameters": {
            "type": "object",
            "properties": {
                "switch": {
                    "type": "boolean",
                    "enum": [True, False],
                    "description": "是否打开摄像头",
                }
            },
            "required": ["switch"],
        }
    }
}]

aigc = Aily(".env")
aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.on_function_call.subscribe(lambda i: function_call_handler(i))

aigc.register_tools(tools)
# 为了方便测试，直接设定了必须调用函数
aigc.choice_tool({"type": "function", "function": {"name": "get_picture"}})

aigc.run()
