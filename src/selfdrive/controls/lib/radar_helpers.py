from common.numpy_fast import mean
from common.kalman.simple_kalman import KF1D
import statistics
import numpy as np
import datetime

# Default lead acceleration decay set to 50% at 1s
_LEAD_ACCEL_TAU = 1.5

# radar tracks
SPEED, ACCEL = 0, 1   # Kalman filter states enum

# stationary qualification parameters
v_ego_stationary = 4.   # no stationary object flag below this speed

RADAR_TO_CENTER = 2.7   # (deprecated) RADAR is ~ 2.7m ahead from center of car
RADAR_TO_CAMERA = 1.52   # RADAR is ~ 1.5m ahead from center of mesh frame

LEAD_DATA_MAX_COUNT = 150
DATA_AVERAGING_RATE = 30
LEAD_DATA_COUNT_BEFORE_VALID = 4

PROGRAM_START = datetime.datetime.now()


def weightedAverage(data):
  Weights = list(range(1, len(data) + 1))
  return np.average(data, weights=Weights)

def reject_outliers(data, m=2.):
  data = np.array(data)
  d = np.abs(data - np.median(data))
  mdev = np.median(d)
  s = d / mdev if mdev else np.zeros(len(d))
  return data[s < m].tolist()

class Track():
  def __init__(self, v_lead, kalman_params):
    self.cnt = 0
    self.aLeadTau = _LEAD_ACCEL_TAU
    self.K_A = kalman_params.A
    self.K_C = kalman_params.C
    self.K_K = kalman_params.K
    self.kf = KF1D([[v_lead], [0.0]], self.K_A, self.K_C, self.K_K)

  def update(self, d_rel, y_rel, v_rel, v_lead, measured):
    # relative values, copy
    self.dRel = d_rel   # LONG_DIST
    self.yRel = y_rel   # -LAT_DIST
    self.vRel = v_rel   # REL_SPEED
    self.vLead = v_lead
    self.measured = measured   # measured or estimate

    # computed velocity and accelerations
    if self.cnt > 0:
      self.kf.update(self.vLead)

    self.vLeadK = float(self.kf.x[SPEED][0])
    self.aLeadK = float(self.kf.x[ACCEL][0])

    # Learn if constant acceleration
    if abs(self.aLeadK) < 0.5:
      self.aLeadTau = _LEAD_ACCEL_TAU
    else:
      self.aLeadTau *= 0.9

    self.cnt += 1

  def get_key_for_cluster(self):
    # Weigh y higher since radar is inaccurate in this dimension
    return [self.dRel, self.yRel*2, self.vRel]

  def reset_a_lead(self, aLeadK, aLeadTau):
    self.kf = KF1D([[self.vLead], [aLeadK]], self.K_A, self.K_C, self.K_K)
    self.aLeadK = aLeadK
    self.aLeadTau = aLeadTau


class Cluster():
  def __init__(self):
    self.tracks = set()

  def add(self, t):
    # add the first track
    self.tracks.add(t)

  # TODO: make generic
  @property
  def dRel(self):
    return mean([t.dRel for t in self.tracks])

  @property
  def yRel(self):
    return mean([t.yRel for t in self.tracks])

  @property
  def vRel(self):
    return mean([t.vRel for t in self.tracks])

  @property
  def aRel(self):
    return mean([t.aRel for t in self.tracks])

  @property
  def vLead(self):
    return mean([t.vLead for t in self.tracks])

  @property
  def dPath(self):
    return mean([t.dPath for t in self.tracks])

  @property
  def vLat(self):
    return mean([t.vLat for t in self.tracks])

  @property
  def vLeadK(self):
    return mean([t.vLeadK for t in self.tracks])

  @property
  def aLeadK(self):
    if all(t.cnt <= 1 for t in self.tracks):
      return 0.
    else:
      return mean([t.aLeadK for t in self.tracks if t.cnt > 1])

  @property
  def aLeadTau(self):
    if all(t.cnt <= 1 for t in self.tracks):
      return _LEAD_ACCEL_TAU
    else:
      return mean([t.aLeadTau for t in self.tracks if t.cnt > 1])

  @property
  def measured(self):
    return any(t.measured for t in self.tracks)

  def get_RadarState(self, model_prob=0.0):
    return {
      "dRel": float(self.dRel),
      "yRel": float(self.yRel),
      "vRel": float(self.vRel),
      "vLead": float(self.vLead),
      "vLeadK": float(self.vLeadK),
      "aLeadK": float(self.aLeadK),
      "status": True,
      "fcw": self.is_potential_fcw(model_prob),
      "modelProb": model_prob,
      "radar": True,
      "aLeadTau": float(self.aLeadTau)
    }

  def get_RadarState_from_vision(self, lead_msg, v_ego, vLeads, Dists):
    # this data is a little noisy, let's smooth it out
    finalv = v_ego
    finald = 150.0
    finalp = 0.0

    if lead_msg.prob < 0.5:
      Dists.clear()
      vLeads.clear()
    else:
      Dists.append(lead_msg.x[0])
      vLeads.append(lead_msg.v[0] - v_ego)
      if len(Dists) > LEAD_DATA_MAX_COUNT:
        Dists.pop(0)
        vLeads.pop(0)
      # how much lead car values do we want to average?
      dcount = min(len(Dists), max(LEAD_DATA_COUNT_BEFORE_VALID, int(round(DATA_AVERAGING_RATE * lead_msg.xStd[0]))))
      vcount = min(len(vLeads), max(LEAD_DATA_COUNT_BEFORE_VALID, int(round(DATA_AVERAGING_RATE * lead_msg.vStd[0]))))
      finald = weightedAverage(Dists[-dcount:])
      finalv = weightedAverage(vLeads[-vcount:])
      # only consider we've got a lead when we've collected some data on it
      if len(vLeads) >= LEAD_DATA_COUNT_BEFORE_VALID:
        finalp = float(lead_msg.prob)

    return {
      "dRel": float(finald - RADAR_TO_CAMERA),
      "yRel": float(-lead_msg.y[0]),
      "vRel": float(finalv),
      "vLead": float(finalv + v_ego),
      "vLeadK": float(lead_msg.vStd[0]),
      "aLeadK": float(lead_msg.xStd[0]),
      "aLeadTau": float((datetime.datetime.now() - PROGRAM_START).total_seconds()),
      "fcw": False,
      "modelProb": finalp,
      "radar": False,
      "status": True
    }

  def __str__(self):
    ret = f"x: {self.dRel:4.1f}  y: {self.yRel:4.1f}  v: {self.vRel:4.1f}  a: {self.aLeadK:4.1f}"
    return ret

  def potential_low_speed_lead(self, v_ego):
    # stop for stuff in front of you and low speed, even without model confirmation
    # Radar points closer than 0.75, are almost always glitches on toyota radars
    return abs(self.yRel) < 1.0 and (v_ego < v_ego_stationary) and (0.75 < self.dRel < 25)

  def is_potential_fcw(self, model_prob):
    return model_prob > .9
