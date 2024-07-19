from pydantic import BaseModel


class STTBaiduOptions(BaseModel):
    key: str
    secret_key: str
    app_id: str = ""
    dev_pid: int = 1537


class STTAzureOptions(BaseModel):
    key: str
    location: str = "eastasia"
    lang: str = "zh-CN"


class STTWhisperOptions(BaseModel):
    key: str
    url: str = None


class TTSBaiduOptions(BaseModel):
    key: str
    secret_key: str
    app_id: str = ""
    lang: str = "zh"
    options: dict = None


class TTSEdgeOptions(BaseModel):
    voice: str = "zh-CN-XiaoxiaoNeural"


class TTSOpenAIOptions(BaseModel):
    key: str
    voice: str = "fable"
    url: str = None
    response_format: str = "mp3"


class TTSAzureOptions(BaseModel):
    key: str
    location: str = "eastasia"
    lang: str = "zh-CN"
    voice: str = "zh-CN-XiaoxiaoNeural"
