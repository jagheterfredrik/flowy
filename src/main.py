# coding: utf8
__version__ = '0.2'

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.utils import platform

from jnius import autoclass

from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer

import os
import time
# os.environ["OPENPILOT_PREFIX"] = "."
os.environ["ZMQ"] = "1"

import cereal.messaging as messaging
import time
import msgq
import concurrent.futures
pm = messaging.PubMaster(['modelV2'])
from opendbc.car.car_helpers import get_demo_car_params
from openpilot.common.params import Params
from openpilot.selfdrive.car.helpers import convert_to_capnp


# ps = msgq.pub_sock("a")

# import zmq

# context = zmq.Context()
# socket = context.socket(zmq.PUB)
# socket.connect("tcp://127.0.0.1:5556")


SERVICE_NAME = u'{packagename}.Service{servicename}'.format(
    packagename=u'org.kivy.oscservice',
    servicename=u'Radard'
)

PONG_SERVICE = u'{packagename}.Service{servicename}'.format(
    packagename=u'org.kivy.oscservice',
    servicename=u'Pong'
)

KV = '''
BoxLayout:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: None
        height: '30sp'
        Button:
            text: 'start service'
            on_press: app.start_service()
        Button:
            text: 'stop service'
            on_press: app.stop_service()

    ScrollView:
        Label:
            id: label
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.size[0], None

    BoxLayout:
        size_hint_y: None
        height: '30sp'
        Button:
            text: 'ping'
            on_press: app.send()
        Button:
            text: 'clear'
            on_press: label.text = ''
        Label:
            id: date

'''


class ClientServerApp(App):
    def build(self):
        self.service = None
        # self.start_service()

        self.server = server = OSCThreadServer()
        server.listen(
            address=b'localhost',
            port=3002,
            default=True,
        )

        server.bind(b'/message', self.display_message)
        server.bind(b'/date', self.date)

        self.client = OSCClient(b'localhost', 3000)
        self.root = Builder.load_string(KV)

        # Clock.schedule_interval(self.my_callback, 0.5)

        return self.root

    def my_callback(self, dt):
        msg = sm.update()
        print('you rang', str(msg))
        if self.root and msg:
            self.root.ids.label.text += '{}\n'.format(str(msg).decode('utf8'))

    def start_service(self):
        if platform == 'android':
            service = autoclass(SERVICE_NAME)
            self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
            argument = ''
            service.start(self.mActivity, argument)
            self.service = service

        elif platform in ('linux', 'linux2', 'macos', 'win'):
            from runpy import run_path
            from threading import Thread
            self.service = Thread(
                target=run_path,
                args=['src/service.py'],
                kwargs={'run_name': '__main__'},
                daemon=True
            )
            self.service.start()
        else:
            raise NotImplementedError(
                "service start not implemented on this platform"
            )

    def stop_service(self):
        # if self.service:
        #     if platform == "android":
        #         self.service.stop(self.mActivity)

        service = autoclass(PONG_SERVICE)
        self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(self.mActivity, argument)

    def send(self, *args):
        self.client.send_message(b'/ping', [])

        # sock = "peripheralState"
        # pub_sock = messaging.pub_sock(sock)
        # sm = messaging.SubMaster([sock,])
        Params().put("CarParams", convert_to_capnp(get_demo_car_params()).to_bytes())
        time.sleep(1)

        dat = messaging.new_message('modelV2')
        dat.valid = True
        # fake peripheral state data
        dat.modelV2 = {
        }
        pm.send('modelV2', dat.to_bytes())
        # pub_sock.send(dat.to_bytes())
        # sm.update(1000)
        # print(sm[sock])

        # socket.send_string("adambanan")

        # ps.send(b'asdf')


    def display_message(self, message):
        if self.root:
            self.root.ids.label.text += '{}\n'.format(message.decode('utf8'))

    def date(self, message):
        if self.root:
            self.root.ids.date.text = message.decode('utf8')


if __name__ == '__main__':
    ClientServerApp().run()
