from setuptools import setup, find_packages

setup(
    name="aily-py",
    version="2.0.1",
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*"]
    ),
    entry_points='''
        [console_scripts],
        aily=aily.main:main
    ''',
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
        "baidu-aip",
        "chardet",
        "edge-tts == 6.1.10"
    ],
    author="stao",
    author_email="werewolf_st@hotmail.com",
    description="Aily is a Python library for AI development.",
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url="https://aily.pro",
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
)
