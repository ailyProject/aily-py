# aily-py

## 安装

```
pip install aily-py
```

## 快速开始

> 复制example/.env.sample到项目根目录下，并重命名为.env，配置相关必填参数

```python
from aily import Aily
from loguru import logger
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


aily = Aily(".env")
aily.on_record_end.subscribe(lambda i: record_end_handler(i))
aily.on_invoke_end.subscribe(lambda i: invoke_end_handler(i))
aily.run()

```


## Aily类

### 类初始化

- 配置文件形式初始化(推荐，便于与提供[aily_config_tool](https://github.com/ailyProject/aily-config-tool)工具配合使用)

  ```python
  aily = Aily(".env")
  ```


- 直接初始化

  ```python
  aily = Aily()
  ```


### 环境变量配置说明

> .env配置文件各参数说明

- `PORT`：串口设备路径(必填)
- `BAUDRATE`: 波特率(必填)
- `SERIAL_TIMEOUT`: 串口读取超时时间
- `CONVERSATION_MODE`: 对话模式(`single`、`multi`、`manual`)
- `LLM_URL`: 大模型服务地址(必填)
- `LLM_KEY`: 大模型key(必填)
- `LLM_MODEL`: 使用的模型(必填)
- `LLM_TEMPERATURE`: 温度
- `LLM_PRE_PROMPT`: 前置提示
- `LLM_MAX_TOKEN_LENGTH`: 最大token长度
- `LLM_VISION_URL`: 视觉模型服务地址
- `LLM_VISION_KEY`: 视觉模型key
- `LLM_VISION_MODEL`: 视觉模型

- `STT_MODEL`: 语音转文字使用的模型(必填), 可选值为：`baidu`, `azure`, `whisper`
- `STT_KEY`: 语音转文字使用的key
- `STT_URL`: 语音转文字服务地址
- `STT_SECRET_KEY`: 语音转文字使用的secret_key(baidu需要)
- `STT_LANG`: 语音转文字使用的语言，如'zh-CN',根据选择的模型填写
- `STT_LOCATION`: 选择的模型为azure时需要填写，默认为eastasia

- `TTS_MODEL`: 文字转语音使用的模型(必填), 可选值为：`baidu`, `edge`, `tts-1`，`azure`
- `TTS_URL`: 文字转语音服务的地址
- `TTS_KEY`: 文字转语音服务的key
- `TTS_ROLE`: 文字转语音角色，根据模型提供的选择
- `TTS_LANG`: 语言类型，如'zh-CN'
- `TTS_LOCATION`: 选择的模型为azure时需要填写，默认为eastasia

- `USE_AILY_TTS`: 是否使用aily的tts模块
- `TTS_PORT`: aily tts模块的串口设备路径
- `TTS_BAUDRATE`: aily tts模块的波特率

- `DB_NAME`: 数据库名称(使用的是sqlite来保存对话记录)
- `WAIT_WORDS_LOOP_PLAY`: 等待音是否循环播放


### Aily对象可订阅的事件

- `wakeup`: 唤醒事件
- `on_record_begin`: 语音录制开始事件
- `on_record_end`: 语音录制结束事件
- `on_play_begin`: 语音播放开始事件
- `on_play_end`: 语音播放结束事件
- `on_recognition`: 离线指令识别
- `on_direction`: 音源方向识别
- `on_invoke_begin`: LLM调用开始事件
- `on_invoke_end`: LLM调用结束事件
- `on_function_call`: 功能调用事件
- `on_custom_invoke`: 自定义模型调用事件
- `on_custom_invoke_vision`: 自定义视觉模型调用事件
- `on_invalid_msg`: 无效语音事件(语音转文字后的结果为空，则发起此事件)
- `on_conversation_records`: 对话记录获取事件


### Aily对象属性

> 配置文件方式初始化，相关参数配置可省略

- `port`：配置串口设备路径
- `baudrate`：配置波特率
- `serial_timeout`：配置串口读取超时时间
- `conversation_mode`：配置对话模式，值为：`single/multi/manual`，默认为 `single`
- `llm_server`：配置大模型服务地址
- `llm_key`：配置大模型key
- `llm_model`：配置使用的模型
- `llm_temperature`：配置温度
- `llm_pre_prompt`：配置系统提示词
- `llm_max_token_length`：配置最大token长度
- `llm_vision_server`：配置视觉模型服务地址
- `llm_vision_key`：配置视觉模型key
- `llm_vision_model`：配置视觉模型
- `use_aily_tts `：配置是否使用aily tts模块，值为：`True/False`，默认为 `False`
- `tts_port `：配置aily tts串口
- `tts_baudrate`：配置aily tts波特率
- `custom_invoke`：是否自定义模型调用，值为：`True/False`，默认为 `False`
- `custom_invoke_vision`：是否自定义视觉模型调用，值为：`True/False`，默认为 `False`
- `auto_play_wait_words`: 配置是否自动播放等待音，值为：`True/False`，默认为 `True`
- `loop_play_wait_words`: 配置等待音是否循环播放，值为：`True/False`，默认为 `False`
- `conversation_expired_at`: 配置对话记录过期时间，单位为秒，默认为 `300`


### Aily对象方法

- `init()`: 执行初始化
- `run()`: 启动服务
- `send_message(message)`: 发送消息到LLM
- `play(data)`: 播放tts
- `play_mp3(data)`: 播放mp3，如等待音，提示音等
- `invoke_reply(message)`: 自定义模型调用后的结果反馈
- `reply_message(message)`: function call函数处理后的结果反馈
- `register_tools(tools)`: 注册工具
- `choice_tool(tool_name)`: 选择工具


## 工具调用

### 语音转文字

#### speech_to_text

- 使用方法
```
from aily.tools import speech_to_text
from aily.models import STTBaiduOptions, ...
speech_to_text(pcm_data, model='baidu', options=STTBaiduOptions)
```

- 说明
    - pcm_data：为pcm文件内容
    - model：选择的转换模型，默认提供的可选有`baidu`、`azure`、`whisper`
    - options：模型参数，模型参数的选择根据模型的选择有些差异
        - baidu: `https://cloud.baidu.com/doc/SPEECH/s/0lbxfnc9b`
        - azure: `https://github.com/Uberi/speech_recognition`
        - whisper: `https://platform.openai.com/docs/guides/speech-to-text/quickstart`



### 文字转语音

#### text_to_speech

- 使用方法
```
from aily.tools import text_to_speech
from aily.models import TTSBaiduOptions, ...
text_to_speech(text, model='baidu', options=TTSBaiduOptions)
```

- 说明
    - text: 需要转换为语音的文本
    - model：选择的转换模型，默认提供的可选有`baidu`、`edge`、`tts-1`、`azure`
    - options: 模型参数，模型参数的选择根据模型的选择有些差异
        - baidu: `https://cloud.baidu.com/doc/SPEECH/s/plbxhh4be`
        - edge: `https://github.com/rany2/edge-tts`
        - tts-1: `https://platform.openai.com/docs/guides/text-to-speech/overview`
        - azure: `https://learn.microsoft.com/zh-cn/azure/ai-services/speech-service/get-started-text-to-speech?tabs=windows%2Cterminal&pivots=programming-language-python`
