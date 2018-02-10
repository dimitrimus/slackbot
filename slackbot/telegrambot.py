#!/usr/bin/python
# -*- coding: utf-8

import time
import threading
import logging

import requests

from abstract_bot import AbstractBot, AbstractMessage


class TelegramBot(AbstractBot):
    _small_retry_interval_secs = 1
    _large_retry_interval_secs = 2

    def __init__(self, token):
        super(TelegramBot, self).__init__()

        self._thread = threading.Thread(target=self._run)
        self._is_thread_started = False

        self._token = token
        self._base_url = 'https://api.telegram.org/bot%(token)s' % {'token': self._token}

        self._start_timestamp = int(time.time())

    def connect(self):
        self._start_update_thread()
        super(TelegramBot, self).connect()

    def _start_update_thread(self):
        self._thread.start()

    def _run(self):
        self._is_thread_started = True
        offset = 0
        while self._is_thread_started:
            url = self._base_url + '/getUpdates?offset=%(offset)d' % {'offset': offset}
            r = requests.get(url)
            if r.status_code != 200:
                logging.debug('http error: %s' % r.text)
                time.sleep(self._small_retry_interval_secs)
                continue

            response = r.json()
            if response['ok'] is not True:
                logging.debug('http error: %s' % r.text)
                time.sleep(self._small_retry_interval_secs)
                continue

            result = response['result']
            for item in result:
                self._process_message(item['message'])
                offset = item['update_id'] + 1

            sleep_interval = self._small_retry_interval_secs if result else self._large_retry_interval_secs
            time.sleep(sleep_interval)

    def _process_message(self, message):
        if message['date'] < self._start_timestamp:
            return  # filter messages with date earlier than bot started
        self.handle_message(AbstractMessage(channel_id=message['chat']['id'], text=message['text']))

    def _stop_update_thread(self):
        self._is_thread_started = False
        self._thread.join()

    def disconnect(self):
        self._stop_timers()
        self._stop_update_thread()

    def is_connected(self):
        return self._is_thread_started

    def send_message(self, channel_id, text):
        """
        Sends message with the content <text> to the channel with <channel_id>
        """
        url = self._base_url + '/sendMessage'
        message = {
            'chat_id': channel_id,
            'text': text
        }
        r = requests.post(url, json=message)
        if r.status_code != 200:
            logging.debug('http error: %s' % r.text)
