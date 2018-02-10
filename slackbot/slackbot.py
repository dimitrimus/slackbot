#!/usr/bin/python
# -*- coding: utf-8

import json
import urllib2
import websocket
import threading
import logging

from abstract_bot import AbstractBot, AbstractMessage


class SlackBot(AbstractBot):
    _message_counter = 1

    def __init__(self, token):
        super(SlackBot, self).__init__()
        
        self._websocket_app = None
        self._thread = threading.Thread(target=self._run)
        self._token = token

    def connect(self):
        url_template = 'https://slack.com/api/rtm.start?simple_latest=true&no_unreads=true&token=%s'
        req = urllib2.Request(url_template % self._token)
        response = urllib2.urlopen(req)
        body = response.read()
        slack_team_info = json.loads(body)

        websocket_url = slack_team_info['url']
        self._start_websocket_app(websocket_url)

        super(SlackBot, self).connect()

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
        logging.debug('websocket message: %s' % message)

        msg = json.loads(message)
        msg_type = msg.get('type', None)

        if msg_type == 'message':
            if 'reply_to' in msg:
                return  # Skip the last sent message (by bot) - don't need to check whether it was successfully sent
            self.handle_message(AbstractMessage(channel_id=message['channel'], text=message['text']))
        elif msg_type == 'reconnect_url':
            pass  # experimental

    def _on_error(self, ws, error):
        logging.debug('websocket error: %s' % error)

    def _on_close(self, ws):
        logging.debug('websocket closed')

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
