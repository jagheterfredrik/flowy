from cereal import car
from common.params import Params
from selfdrive.manager.process import ManagerProcess
from common.system import is_android

def driverview(started: bool, params: Params, CP: car.CarParams) -> bool:
  return params.get_bool("IsDriverViewEnabled")  # type: ignore

def notcar(started: bool, params: Params, CP: car.CarParams) -> bool:
  return CP.notCar  # type: ignore

def logging(started, params, CP: car.CarParams) -> bool:
  run = (not CP.notCar) or not params.get_bool("DisableLogging")
  return started and run

def useModelParseD():
  #return False #if we are running externally
  return Params().get_bool("F3")

procs = [
  ManagerProcess("controlsd", "controlsd"),
  ManagerProcess("plannerd", "plannerd"),
  ManagerProcess("radard", "radard"),
  ManagerProcess("calibrationd", "calibrationd"),
  ManagerProcess("modelparsed", "./selfdrive/modeld/modelparsed", enabled=useModelParseD()),
  ManagerProcess("clocksd", "./system/clocksd/clocksd"),
  ManagerProcess("proclogd", "./system/proclogd/proclogd"),
  ManagerProcess("logmessaged", "logmessaged", offroad=True),
  ManagerProcess("thermald_", "thermald_", offroad=True),
  #ManagerProcess("statsd", "statsd", offroad=True),
  ManagerProcess("keyvald", "keyvald", offroad=True),
  ManagerProcess("flowpilot", "./gradlew", args=["desktop:run"], rename=False, offroad=True, platform=["desktop"], pipe_std=False),
  ManagerProcess("pandad", "pandad", offroad=True),
  #ManagerProcess("loggerd", "./selfdrive/loggerd/loggerd", enabled=True, onroad=False, callback=logging),
  #ManagerProcess("uploader", "uploader", enabled=is_android(), offroad=True),
  #ManagerProcess("deleter", "deleter", enabled=True, offroad=True),
  ManagerProcess("ubloxd", "./selfdrive/locationd/ubloxd", onroad=False),
  ManagerProcess("laikad", "laikad", enabled=False),
  #ManagerProcess("paramsd", "paramsd", enabled=False),
  ManagerProcess("torqued", "torqued", enabled=False),
  #ManagerProcess("locationd", "./selfdrive/locationd/locationd", enabled=False),
]

platform = "android" if is_android() else "desktop" 
managed_processes = {p.name: p for p in procs if platform in p.platform}
