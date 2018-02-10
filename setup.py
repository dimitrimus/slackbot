from distutils.core import setup

setup(
    name='SlackBot',
    version='0.2.0',
    author='Dmitry Sychev',
    author_email='dee.sychev@gmail.com',
    packages=['slackbot'],
    description='Tiny lib for making fun slack or telegram bots.',
    install_requires=[
        "websocket-client == 0.35.0",
        "requests == 2.7.0",
    ],
)
