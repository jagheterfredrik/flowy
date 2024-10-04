import os
import sys
import runpy

# Force ZMQ
os.environ["ZMQ"] = "1"

# DBC lookup requires this
os.environ["BASEDIR"] = "./"

runpy.run_module("openpilot.selfdrive.controls.plannerd", run_name= "__main__")