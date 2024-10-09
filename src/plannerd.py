import os
import runpy

# DBC lookup requires this
os.environ["BASEDIR"] = "./"

runpy.run_module("selfdrive.controls.plannerd", run_name= "__main__")