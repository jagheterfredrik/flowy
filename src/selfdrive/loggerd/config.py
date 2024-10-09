import os
from common.path import flowpilot_root
from system.hardware import PC
from common.path import external_android_storage
from common.system import is_android

if os.environ.get('LOG_ROOT', False):
  ROOT = os.environ['LOG_ROOT']
else:
  ROOT = os.path.join(flowpilot_root(), ".flowdrive", "media", "0", "realdata")

if is_android():
  VIDEO_LOGS = os.path.join(external_android_storage(), "flowpilot", ".flowdrive", "media", "0", "videos")
else:
  VIDEO_LOGS = os.path.join(os.path.dirname(ROOT), "videos")
os.makedirs(ROOT, exist_ok=True)
os.makedirs(VIDEO_LOGS, exist_ok=True)

VIDEO_EXTENSION = "mp4"
LOG_FORMAT = "%Y-%m-%d--%H-%M-%S.%f"
VIDEO_LOG_FORMAT = f"%Y-%m-%d--%H-%M-%S.%f.{VIDEO_EXTENSION}"

CAMERA_FPS = 20
SEGMENT_LENGTH = 60

STATS_DIR_FILE_LIMIT = 10000
STATS_SOCKET = "ipc:///tmp/stats"
STATS_DIR = os.path.join(flowpilot_root(), ".flowdrive", "stats")
STATS_FLUSH_TIME_S = 60

def get_available_percent(default=None):
  try:
    statvfs = os.statvfs(ROOT)
    available_percent = 100.0 * statvfs.f_bavail / statvfs.f_blocks
  except OSError:
    available_percent = default

  return available_percent


def get_available_bytes(default=None):
  try:
    statvfs = os.statvfs(ROOT)
    available_bytes = statvfs.f_bavail * statvfs.f_frsize
  except OSError:
    available_bytes = default

  return available_bytes
