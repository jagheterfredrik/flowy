import os

def flowpilot_root():
    return "/data/data/ai.flow.android/files/app"

def internal(path):
    return os.path.join(flowpilot_root(), path)

def external_android_storage():
    return "/sdcard"

BASEDIR = flowpilot_root()
