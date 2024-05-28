import base64

from aily import AIGC
from aily.tools import speex_decoder, speech_to_text, text_to_speech
from loguru import logger


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def function_call_handler(event):
    logger.info("收到函数调用请求：{0}".format(event))
    call_id = event["id"]
    if event["name"] == "get_picture":
        logger.debug("调用摄像头拍照")
        # TODO 调用摄像头拍照
        
        # 方式一：直接返回图片的URL
        # content = {
        #     "url": 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg'
        # }
        
        # 方式二：返回图片的base64编码
        image = encode_image("./vision_test_image.jpg")
        content = {
            "url": f"data:image/jpeg;base64,{image}"
        }
        aigc.reply_message(call_id, content, "image")


def record_end_handler(data):
    voice_data = speex_decoder(data)
    text = speech_to_text(voice_data)
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
        "description": "Get a picture from Camera",
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


aigc = AIGC(".func_env")
aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.on_function_call.subscribe(lambda i: function_call_handler(i))

aigc.register_tools(tools)
aigc.choice_tool({"type": "function", "function": {"name": "get_picture"}})

aigc.run()
