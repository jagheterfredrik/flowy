import runpy

import time
from common.params import Params
params = Params()

from selfdrive.controls.radard import main

while True:
    controlsd_onroad = params.get_bool("IsOnroad")
    if controlsd_onroad:
        main()
        break
    time.sleep(.1)
