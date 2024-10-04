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
import sys
# os.environ["OPENPILOT_PREFIX"] = "."
os.environ["ZMQ"] = "1"
# os.environ["LD_LIBRARY_PATH"] = os.path.dirname(os.path.realpath(__file__))+"/openpilot"
sys.path.append('./openpilot')
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/openpilot')
# print('libpath', os.environ["LD_LIBRARY_PATH"])
print('syspath', sys.path)

import cereal.messaging as messaging
import time
import msgq
import concurrent.futures
pm = messaging.PubMaster(['modelV2'])

from openpilot.common.params import Params
from cereal import car


# ps = msgq.pub_sock("a")

# import zmq

# context = zmq.Context()
# socket = context.socket(zmq.PUB)
# socket.connect("tcp://127.0.0.1:5556")


RADARD_SERVICE = u'{packagename}.Service{servicename}'.format(
    packagename=u'org.kivy.oscservice',
    servicename=u'Radard'
)

CONTROLSD_SERVICE = u'{packagename}.Service{servicename}'.format(
    packagename=u'org.kivy.oscservice',
    servicename=u'Controlsd'
)

PLANNERD_SERVICE = u'{packagename}.Service{servicename}'.format(
    packagename=u'org.kivy.oscservice',
    servicename=u'Plannerd'
)

PONG_SERVICE = u'{packagename}.Service{servicename}'.format(
    packagename=u'org.kivy.oscservice',
    servicename=u'Pong'
)

KV = '''
BoxLayout:
    orientation: 'vertical'
    position_hint: {'center_x':0.5, 'center_y':0.5}
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '120sp'
        Button:
            text: 'Start radard'
            on_press: app.start_radard()
            height: '60sp'
            font_size: '60'
        Button:
            text: 'Start radar listener'
            on_press: app.start_service()
            height: '60sp'
            font_size: '60'
        Button:
            text: 'Start controlsd'
            on_press: app.start_controlsd()
            height: '60sp'
            font_size: '60'
        Button:
            text: 'Start plannerd'
            on_press: app.start_plannerd()
            height: '60sp'
            font_size: '60'
        Button:
            text: 'Send car params'
            on_press: app.send_car_params()
            height: '60sp'
            font_size: '60'
        Button:
            text: 'Misc'
            on_press: app.send_modelv2()
            height: '60sp'
            font_size: '60'

'''


class ClientServerApp(App):
    def build(self):
        self.service = None

        self.root = Builder.load_string(KV)

        return self.root

    def start_radard(self):
        service = autoclass(RADARD_SERVICE)
        self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(self.mActivity, argument)
        self.service = service

    def start_service(self):
        service = autoclass(PONG_SERVICE)
        self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(self.mActivity, argument)

    def start_controlsd(self):
        service = autoclass(CONTROLSD_SERVICE)
        self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(self.mActivity, argument)

    def start_plannerd(self):
        service = autoclass(PLANNERD_SERVICE)
        self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
        argument = ''
        service.start(self.mActivity, argument)

    def send_car_params(self, *args):
        cp = car.CarParams.new_message()

        safety_config = car.CarParams.SafetyConfig.new_message()
        safety_config.safetyModel = car.CarParams.SafetyModel.allOutput
        cp.safetyConfigs = [safety_config]
        cp.carName = 'volkswagen'
        from opendbc.car.volkswagen.values import CAR
        cp.carFingerprint = CAR.VOLKSWAGEN_PASSAT_MK8

        Params().put("CarParams", cp.to_bytes())
 
    def send_modelv2(self):
        dat = messaging.new_message('modelV2')
        dat.valid = True
        # fake peripheral state data
        dat.modelV2 = {
        }
        pm.send('modelV2', dat.to_bytes())


if __name__ == '__main__':
    ClientServerApp().run()
