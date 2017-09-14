#!/usr/bin/python
# -*- coding: utf-8

import json
import urllib2
import websocket
import threading
import uuid
import datetime
import logging
import time

from threading import Timer
from collections import defaultdict
from functools import wraps


class SlackBot(object):
    _message_counter = 1

    def __init__(self, token):
        self._websocket_app = None
        self._thread = threading.Thread(target=self._run)
        self._token = token

        self._incoming_message_handlers = defaultdict(list)
        self._schedule_timers = {}

    def connect(self):
        url_template = 'https://slack.com/api/rtm.start?simple_latest=true&no_unreads=true&token=%s'
        req = urllib2.Request(url_template % self._token)
        response = urllib2.urlopen(req)
        body = response.read()
        slack_team_info = json.loads(body)

        websocket_url = slack_team_info['url']
        self._start_websocket_app(websocket_url)

        self._start_timers()

    def _start_websocket_app(self, websocket_url):
        self._websocket_app = websocket.WebSocketApp(websocket_url,
                                                     on_message=self._on_message,
                                                     on_error=self._on_error,
                                                     on_close=self._on_close)
        self._thread.start()

    def _run(self):
        self._websocket_app.run_forever()

    def _stop_websocket_app(self):
        self._websocket_app.close()
        self._thread.join()

    def disconnect(self):
        self._stop_timers()
        self._stop_websocket_app()
        self._websocket_app = None

    def is_connected(self):
        return self._websocket_app and self._websocket_app.sock.connected

    def _on_message(self, ws, message):
        logging.debug('websocket message: %s' % message)

        msg = json.loads(message)
        msg_type = msg.get('type', None)

        if msg_type == 'message':
            if 'reply_to' in msg:
                return  # Skip the last sent message (by bot) - don't need to check whether it was successfully sent
            self._handle_message(ws, msg)
        elif msg_type == 'reconnect_url':
            pass  # experimental

    def _on_error(self, ws, error):
        logging.debug('websocket error: %s' % error)

    def _on_close(self, ws):
        logging.debug('websocket closed')

    def _handle_message(self, ws, message):
        """
        Income message format:
        
         {
           "type": "message",
           "channel": "C0Z87P9QX",
           "user": "U0Z8J9602",
           "text": "привет",
           "ts": "1460149913.000003",
           "team": "T0Z6RJS83"
         }
        """
        channel_id = message['channel']
        text = message['text']

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
        """
        Sends message with the content <text> to the channel with <channel_id>
        """
        response_msg = {
            'id': self._message_counter,
            'type': 'message',
            'channel': channel_id,
            'text': text
        }
        self._websocket_app.sock.send(json.dumps(response_msg))
        self._message_counter += 1

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
                time.sleep(1)
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

        today_schedule_datetime = datetime.datetime(year=now.year, month=now.month, day=now.day,
                                                    hour=schedule_time.hour, minute=schedule_time.minute,
                                                    microsecond=schedule_time.microsecond)

        if today_schedule_datetime > now:
            schedule_delta = today_schedule_datetime - now
        else:
            tomorrow_schedule_datetime = today_schedule_datetime + datetime.timedelta(days=1)
            schedule_delta = tomorrow_schedule_datetime - now

        return schedule_delta.seconds

    def _start_timers(self):
        for timer in self._schedule_timers.values():
            timer.start()

    def _stop_timers(self):
        for timer in self._schedule_timers.values():
            timer.cancel()
