from setuptools import setup, find_packages

setup(
    name="aily-py",
    version="2.0.0-beta",
    packages=find_packages(
        where='src',
        include=['*'],
        exclude=['tests']
    ),
    install_requires=[
        "python-dotenv == 1.0.1",
        "aiohttp == 3.9.3",
        "reactivex == 4.0.4",
        "tiktoken == 0.6.0",
        "tenacity == 8.2.3",
        "SpeechRecognition",
        "loguru",
        "requests",
        "pyserial",
        "openai",
        "edge-tts == 6.1.10"
    ]
)
