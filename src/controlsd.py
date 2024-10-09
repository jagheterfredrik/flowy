import os
import runpy

# DBC lookup requires this
os.environ["BASEDIR"] = "./"

import system.version

system.version.get_short_branch = lambda x: "Release"

runpy.run_module("selfdrive.controls.controlsd", run_name= "__main__")