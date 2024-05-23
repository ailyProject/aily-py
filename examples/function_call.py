from aily import AIGC
from aily.tools import speex_decoder, speech_to_text, text_to_speech
from loguru import logger


def function_call_handler(event):
    logger.info(event)


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
        "name": "test_function",
        "description": "This is a test function",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "This is the first parameter"
                },
                "param2": {
                    "type": "string",
                    "description": "This is the second parameter"
                },
            },
            "required": ["param1", "param2"]
        }
    }
}]


aigc = AIGC(".func_env")
aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.on_function_call.subscribe(lambda i: function_call_handler(i))

aigc.register_tools(tools)
aigc.choice_tool("test_function")

aigc.run()
