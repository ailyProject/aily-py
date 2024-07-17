"""
custom vision invoke example
"""

import base64
import subprocess
import time

from aily import Aily
from aily.tools import speech_to_text, text_to_speech
from zhipuai import ZhipuAI
from loguru import logger

def call_camera(output_path):
    subprocess.run(["rpicam-jpeg", "--output", output_path, "--timeout", "2000", "--width", "640", "--height", "480"])


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# def upload_image(image_path):
#     # with open(image_path, "rb") as image_file:
#     #     return image_file.read()
#
#     key = str(int(time.time() * 1000)) + ".jpg"
#     token = q.upload_token(bucket_name, key)
#     ret, info = put_file(token, key, image_path)
#     logger.debug("upload_image: {0}".format(info))
#     return ret["key"]


def function_call_handler(event):
    logger.info("收到函数调用请求：{0}".format(event))
    call_id = event["id"]
    if event["name"] == "get_picture":
        logger.debug("调用摄像头拍照")
        call_camera("./sample.jpg")

        # file_name = upload_image("./sample.jpg")

        # 方式一：直接返回图片的URL
        # content = {
        #     "url": f'http://sfb6drye5.hn-bkt.clouddn.com/{file_name}'
        # }

        # 方式二：返回图片的base64编码
        image = encode_image("./sample.jpg")
        # content = {
        #     "url": f"data:image/jpeg;base64,{image}"
        # }
        content = f"data:image/jpeg;base64,{image}"
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
        "description": "充当眼睛的角色，当需要看到实际的图片或事物才能给出问题的有效回答时，调用此函数",
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


def invoke_vision(data):
    try:
        logger.debug("invoke_vision: {0}".format(data))
        client = ZhipuAI(api_key=data["api_key"])
        response = client.chat.completions.create(
            model=data["model"],  # 填写需要调用的模型名称
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": data["message"]
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data["image_url"]
                            }
                        }
                    ]
                }
            ]
        )

        assistant_message = response.choices[0].message
        logger.debug("assistant_message: {0}".format(assistant_message))

        if assistant_message:
            data = {
                "role": assistant_message.role,
                "content": assistant_message.content,
            }
            aigc.invoke_reply(data)
        else:
            logger.error("invoke_vision error: {0}".format(response))
    except Exception as e:
        logger.error("invoke_vision error: {0}".format(e))


aigc = Aily(".env")
aigc.custom_invoke_vision = True
aigc.set_wait_words("./robot_thinking_16k_s16le.mp3")
aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.on_function_call.subscribe(lambda i: function_call_handler(i))
aigc.on_custom_invoke_vision.subscribe(lambda i: invoke_vision(i))

aigc.register_tools(tools)
# 为了方便测试，直接设定了必须调用函数
aigc.choice_tool({"type": "function", "function": {"name": "get_picture"}})

aigc.run()
