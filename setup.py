from setuptools import setup, find_packages

setup(
    name="agishell",
    version="1.0.0",
    packages=find_packages(
        where='src',
        include=['*'],
        exclude=['tests']
    ),
    install_requires=[
        "python-dotenv == 1.0.1",
        "aiohttp == 3.9.3",
        "reactivex == 4.0.4",
        "loguru",
        "requests",
        "pyserial"
    ]
)
