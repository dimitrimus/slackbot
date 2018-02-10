#!/usr/bin/python
# -*- coding: utf-8

import uuid
import datetime

from threading import Timer
from collections import defaultdict, namedtuple
from functools import wraps


AbstractMessage = namedtuple('AbstractMessage', ['channel_id', 'text'])


class AbstractBot(object):
    def __init__(self):
        self._incoming_message_handlers = defaultdict(list)
        self._schedule_timers = {}

    def connect(self):
        self._start_timers()

    def disconnect(self):
        self._stop_timers()

    def is_connected(self):
        return False

    def handle_message(self, message):
        channel_id = message.channel_id
        text = message.text

        if channel_id in self._incoming_message_handlers:
            handlers = self._incoming_message_handlers[channel_id]
            for handler in handlers:
                handler(text)

    def incoming_message(self, channel_id):
        """
        Decorator for functions which is run when any user post message in the chat with specified channel_id.

        For example:
            bot = SlackBot(config['slack-bot-token'])

            @bot.incoming_message(channel_id='12345678')
            def handler(message):
                bot.send_message('12345678', 'Hello, World!')
        """

        def dec(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)

            self._incoming_message_handlers[channel_id].append(wrapper)
            return wrapper

        return dec

    def send_message(self, channel_id, text):
        pass

    def schedule_period(self, seconds):
        """
        Decorator for functions which is run every <seconds> seconds.

        For example:
            bot = SlackBot(config['slack-bot-token'])

            @bot.schedule_period(5)
            def handler(message):
                bot.send_message('12345678', 'Hello, World!')

            will print 'Hello, World!' every 5 seconds to channel '12345678'
        """

        def dec(fn):
            timer_id = uuid.uuid4().hex

            def wrapper():
                result = fn(datetime.datetime.now())
                if self._schedule_timers[timer_id].is_alive:
                    self._schedule_timers[timer_id] = Timer(seconds, wrapper, ())
                    self._schedule_timers[timer_id].start()
                return result

            self._schedule_timers[timer_id] = Timer(seconds, wrapper, ())
            return wrapper

        return dec

    def schedule_daily(self, at_time):
        """
        Decorator for functions which is run daily on <at_time>.

        For example:
            bot = SlackBot(config['slack-bot-token'])

            @bot.schedule_daily(at_time=datetime.time(hour=22, minute=45))
            def handler(message):
                bot.send_message('12345678', 'Hello, World!')

            will print 'Hello, World!' every 5 seconds to channel '12345678'
        """

        def dec(fn):
            timer_id = uuid.uuid4().hex

            def wrapper():
                result = fn(datetime.datetime.now())
                if self._schedule_timers[timer_id].is_alive:
                    seconds = self._calculate_seconds_to_run(at_time)
                    self._schedule_timers[timer_id] = Timer(seconds, wrapper, ())
                    self._schedule_timers[timer_id].start()
                return result

            seconds = self._calculate_seconds_to_run(at_time)
            self._schedule_timers[timer_id] = Timer(seconds, wrapper, ())
            return wrapper

        return dec

    @staticmethod
    def _calculate_seconds_to_run(schedule_time):
        now = datetime.datetime.now()
        today_schedule_datetime = datetime.datetime(
            year=now.year, month=now.month, day=now.day,
            hour=schedule_time.hour, minute=schedule_time.minute, second=schedule_time.second,
            microsecond=schedule_time.microsecond
        )

        if (today_schedule_datetime - now).total_seconds() > 1:
            schedule_delta = today_schedule_datetime - now
        else:
            tomorrow_schedule_datetime = today_schedule_datetime + datetime.timedelta(days=1)
            schedule_delta = tomorrow_schedule_datetime - now

        return int(schedule_delta.total_seconds())

    def _start_timers(self):
        for timer in self._schedule_timers.values():
            timer.start()

    def _stop_timers(self):
        for timer in self._schedule_timers.values():
            timer.cancel()
