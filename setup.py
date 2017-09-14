from distutils.core import setup

setup(
    name='SlackBot',
    version='0.1.0',
    author='Dmitry Sychev',
    author_email='dee.sychev@gmail.com',
    packages=['slackbot'],
    description='Tiny lib for making fun slack bots.',
    install_requires=[
        "websocket-client == 0.35.0",
    ],
)
