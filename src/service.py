'p4a example service using oscpy to communicate with main application.'
from random import sample, randint
from string import ascii_letters
from time import localtime, asctime, sleep

from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient

CLIENT = OSCClient('localhost', 3002)

# from opendbc.car.car_helpers import interfaces
# interfaces['VOLKSWAGEN_PASSAT_MK8']

import os
os.environ['ZMQ'] = '1'

import cereal.messaging as messaging
sm = messaging.SubMaster(["radarState"])

# import zmq

# context = zmq.Context()
# socket = context.socket(zmq.SUB)
# # accept all topics (prefixed) - default is none
# socket.setsockopt_string(zmq.SUBSCRIBE, "")
# socket.bind("tcp://*:5556")

def ping(*_):
    'answer to ping messages'
    CLIENT.send_message(
        b'/message',
        [
            str().encode('utf8'),
        ],
    )
    # socket.send_pyobj({'a': 'b'})


def send_date():
    'send date to the application'
    CLIENT.send_message(
        b'/message',
        ["hola".encode('utf8'), ],
    )


if __name__ == '__main__':
    SERVER = OSCThreadServer()
    SERVER.listen('localhost', port=3000, default=True)
    SERVER.bind(b'/ping', ping)
    while True:
        # message = ss.receive()
        sm.update(timeout=10000)
        message = sm['radarState']
        if message:
            print("got message", message)
        else:
            print("no message")
