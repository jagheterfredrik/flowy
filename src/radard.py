import os
import sys
import runpy

# Force ZMQ
os.environ["ZMQ"] = "1"

# Radard dynamically loads selfdrive.car.<brand>..
sys.path.append('./openpilot')

runpy.run_module("openpilot.selfdrive.controls.radard", run_name= "__main__")