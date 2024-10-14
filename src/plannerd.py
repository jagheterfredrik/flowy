import os
import runpy

# DBC lookup requires this
os.environ["BASEDIR"] = "./"

import time
from common.params import Params
params = Params()

from selfdrive.controls.plannerd import main

while True:
    controlsd_onroad = params.get_bool("IsOnroad")
    if controlsd_onroad:
        main()
        break
    time.sleep(.1)
