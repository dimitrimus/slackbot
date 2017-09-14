#!/usr/bin/python
# -*- coding: utf-8

import unittest

import sys
sys.path.append('../src/')

from slackbot import SlackBot


class TestSlackbotSuit(unittest.TestCase):

    def test_signals_fetching(self):
        bot = SlackBot('fake-token')

        @bot.incoming_message(channel_id='channel-1')
        def func1(message):
            pass

        @bot.incoming_message(channel_id='channel-2')
        def func2(message):
            pass

        @bot.incoming_message(channel_id='channel-2')
        def func3(message):
            pass

        self.assertEqual(len(bot._incoming_message_handlers), 2)
        self.assertEqual(bot._incoming_message_handlers['channel-1'], [func1])
        self.assertEqual(bot._incoming_message_handlers['channel-2'], [func2, func3])

if __name__ == '__main__':
    unittest.main()
