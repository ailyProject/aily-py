# aily-py

## 安装

```
pip install aily
```

## 快速开始

```python
import os
from aily import AIGC
from aily.tools import speech_to_text, text_to_speech, speex_decoder
from dotenv import load_dotenv

load_dotenv()


def record_end_handler(data):
  # 解码pcm
  voice_data = speex_decoder(data)
  # 语音转文字
  text = speech_to_text(voice_data)
  print("转换后的文字为: {0}".format(text))
  # 调用LLM
  aigc.send_message(text)


def invoke_end_handler(data):
  print("回答：{0}".format(data))
  # 文字转语音
  speech_data = text_to_speech(data)
  # 播放语音
  aigc.play(speech_data)


aigc = AIGC(os.getenv("PORT"))
aigc.on_record_end.subscribe(lambda i: record_end_handler(i))
aigc.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aigc.run()

```

## 可订阅的事件

- wakeup: 唤醒事件
- on_record_begin: 语音录制开始事件
- on_record_end: 语音录制结束事件
- on_play_begin: 语音播放开始事件
- on_play_end: 语音播放结束事件
- on_recognition: 离线指令识别
- on_direction: 音源方向识别
- on_invoke_begin: LLM调用开始事件
- on_invoke_end: LLM调用结束事件

## 参数说明

```python
# 设置大模型key
aigc.set_key("key")
# 设置大模型url
aigc.set_server("url")
# 设置调用的模型
aigc.set_model("model")
# 设置pre_prompt
aigc.set_pre_prompt("pre_prompt")
# 设置temperature
aigc.set_temperature("temperature")
# 设置等待词（可设置文字或音频文件路径）
aigc.set_wait_word("wait_word")
# 设置等待词是否自动播放
aigc.set_wwords_auto_play(True)
# 设置等待词是否循环播放
aigc.set_wwords_loop_play(True)
# 发送消息到LLM
aigc.send_message("message")
# 设置自定义模型调用
aigc.set_custom_llm_invoke("custom_invoke")
```

## 工具调用

> 默认提供了解码工具、语音转文字工具、文字转语音工具

### 解码工具(speex_decoder)

- 参数说明
    - data: speex编码的音频数据
    - result_type: 指定返回的音频类型，目前暂只支持(.mp3/.wav)

### 语音转文字

#### speech_to_text

> 该方法调用的是openai的whisper模型，所以需要提供oepnai的key

- 参数说明
    - filename: 音频文件名
    - file: 音频文件
    - base_url: openai的url
    - api_key: openai的key

#### speech_to_text_sr

> 该方法目前调用的是微软azure的语音服务接口，所以需要提供azure的key

- 参数说明
    - file: 音频文件
    - key: azure的key
    - language: 语言，默认"zh-CN"
    - location: 位置，默认"eastasia"

### 文字转语音(text_to_speech)
> 使用的是edge-tts: https://github.com/rany2/edge-tts

- 参数说明
    - text: 文字
    - voice: 语音类型，默认"zh-CN-XiaoxiaoNeural"
  - 语音类型
    - zh-CN-XiaoxiaoNeural 
    - zh-CN-XiaoyiNeural 
    - zh-CN-YunjianNeural 
    - zh-CN-YunxiNeural 
    - zh-CN-YunxiaNeural 
    - zh-CN-YunyangNeural 
    - zh-CN-liaoning-XiaobeiNeural 
    - zh-CN-shaanxi-XiaoniNeural 
    - zh-HK-HiuGaaiNeural 
    - zh-HK-HiuMaanNeural 
    - zh-HK-WanLungNeural 
    - zh-TW-HsiaoChenNeural 
    - zh-TW-HsiaoYuNeural 
    - zh-TW-YunJheNeural

## 自定义

### 自定义模型调用

> 部分不支持openai风格调用的模型，可以通过自定义模型调用

```python
from zhipuai import ZhipuAI


# 以智普为例，详见example/conversation_llm_zhipu.py
def custom_invoke(**kwargs):
    client = ZhipuAI(api_key=kwargs["api_key"])
    response = client.chat.completions.create(
        model=kwargs["model"],
        messages=kwargs["messages"],
        temperature=kwargs["temperature"],
    )

    return {
        "role": response.choices[0].message.role,
        "content": response.choices[0].message.content,
        "tool_calls": response.choices[0].message.tool_calls
    }

...
aigc.set_custom_llm_invoke(custom_invoke)
...
```
