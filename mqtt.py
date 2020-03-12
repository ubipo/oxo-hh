# -*- coding: utf-8 -*-
"""mqtt.py handles mqtt communication for the OXO game

MQTT is a binary pub/sub topic system.
We create a topic for each game, called a "room".
So if you join game room "fortnite" this class
will pub and sub on the "oxo/fotnite" topic on
the specified mqtt server.

"""

import importlib
import sys
from enum import Enum, unique
from typing import Callable, NamedTuple
from struct import pack, unpack
import traceback
import random

import paho.mqtt.client as mqtt


@unique
class MessageType(Enum):
    """Mqtt game message types"""

    CLAIM_PID = 0
    "Send by player joining a new game. Data: (pid: int)"
    PID_ALREADY_CLAIMED = 1
    "Send in response to CLAIM_PID by pid owner. Data: (pid: int)"

    MAKE_MOVE = 2
    "Move by other player. Data: (x: int, y: int)"


class MqttCommHandlers(NamedTuple):
    """Data class for MqttComm's event handlers"""

    game_start: Callable[[bool], None]
    game_already_started: Callable[[], None]
    move_made: Callable[[int, int], None]


class MqttComm():
    """Handles the OXO game's MQTT communications"""

    host: str
    port: int
    game_name: str
    pid: int
    game_started: bool

    _client: mqtt.Client
    _handlers: MqttCommHandlers
    _uid: int

    def __init__(self, host, port, handlers: MqttCommHandlers):
        self._uid = random.Random().randint(0, (2**(8*8))-1)

        self.host = host
        self.port = port
        self.game_name = None
        self.pid = None
        self.game_started = False
        self._handlers = handlers

        self._client = mqtt.Client()
        self._client.on_connect = lambda *args, **kwargs: self._instance_calback(self._connect_handler, args, kwargs)
        self._client.on_message = lambda *args, **kwargs: self._instance_calback(self._msg_handler, args, kwargs)


    def init(self):
        self._client.connect(self.host, self.port)
        self._client.loop_start()


    def connect(self, game_name: str):
        if self.game_name is not None:
            self._client.unsubscribe(self.game_name)

        self.game_name = game_name
        self._client.subscribe(MqttComm._to_topic(game_name))
        self._claim_pid(0)


    def make_move(self, x: int, y: int):
        self._send(MessageType.MAKE_MOVE, pack('BBB', self.pid, x, y))


    def stop(self):
        self._client.loop_stop()


    def _claim_pid(self, pid: int):
        self.pid = pid
        self._send(MessageType.CLAIM_PID, pack('B', pid))


    def _send(self, msg_type: MessageType, data: bytes):
        payload = (
            pack('Q', self._uid)
            + bytes([msg_type.value])
            + data
        )
        self._client.publish(MqttComm._to_topic(self.game_name), payload)


    def _connect_handler(self, kwargs, client: mqtt.Client, userdata, flags, rc):
        pass


    def _start(self):
        self.game_started = True
        self._handlers.game_start(self.pid == 0)


    def _msg_handler(self, kwargs, client, userdata, msg):
        # We have no control over the arguments; pylint: disable=unused-argument
        payload = msg.payload
        uid = unpack('Q', payload[:8])[0]

        if uid == self._uid:
            # Message is comming from me
            return

        try:
            msg_type = MessageType(payload[8])
        except ValueError:
            return # Not in enum / unknown message type; ignore

        data = msg.payload[9:]

        if msg_type is MessageType.CLAIM_PID:
            pid = MqttComm._extract_pid(data)
            if pid == self.pid:
                self._send(MessageType.PID_ALREADY_CLAIMED, bytes([pid]))
            else:
                if self.pid == 0 and pid == 1:
                    self._start()
        elif msg_type is MessageType.PID_ALREADY_CLAIMED:
            pid = MqttComm._extract_pid(data)
            if self.pid == pid:
                if pid == 0:
                    # Player 1 already claimed, try 2
                    self._claim_pid(1)
                    # Start game; if there's already a player 2 it'll be caught below
                    self._start()
                elif pid == 1:
                    # Player 2 already claimed; game is already in progress
                    self._handlers.game_already_started()
        elif msg_type is MessageType.MAKE_MOVE:
            pid = MqttComm._extract_pid(data)
            x, y = unpack('BB', data[1:])
            if not self.pid == pid:
                self._handlers.move_made(x, y)


    def _instance_calback(self, method, args, kwargs):
        try:
            method(kwargs, *args)
        except Exception: # pylint: disable=broad-except
            print(traceback.format_exc())


    @staticmethod
    def _to_topic(game_name: str):
        return f"oxo-hh/{game_name}"


    @staticmethod
    def _extract_pid(data: bytes):
        return unpack('B', data[:1])[0] % 2


def Net(handlers: MqttCommHandlers):
    """Convenience method for hh"""
    server_addr_py = importlib.util.find_spec("server_address")
    if server_addr_py is not None:
        from server_address import host, port
        return MqttComm(host, port, handlers)
    else:
        sys.exit("No server/port specified. Create a server_address.py file like: \nhost = <host>\nport = <port>")
