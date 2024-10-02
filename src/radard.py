import os
import runpy

# os.environ["OPENPILOT_PREFIX"] = "./"
os.environ["ZMQ"] = "1"
runpy.run_module("openpilot.selfdrive.controls.radard", run_name= "__main__")