#!/usr/bin/env python3
import time
import unittest
from collections import defaultdict
from datetime import datetime
from unittest import mock
from unittest.mock import Mock, patch

from common.params import Params
from laika.constants import SECS_IN_DAY
from laika.downloader import DownloadFailed
from laika.ephemeris import EphemerisType, GPSEphemeris
from laika.gps_time import GPSTime
from laika.helpers import ConstellationId, TimeRangeHolder
from laika.raw_gnss import GNSSMeasurement, read_raw_ublox
from selfdrive.locationd.laikad import EPHEMERIS_CACHE, EphemerisSourceType, Laikad, create_measurement_msg
from selfdrive.test.openpilotci import get_url
from tools.lib.logreader import LogReader


def get_log(segs=range(0)):
  logs = []
  for i in segs:
    logs.extend(LogReader(get_url("4cf7a6ad03080c90|2021-09-29--13-46-36", i)))
  return [m for m in logs if m.which() == 'ubloxGnss']


def verify_messages(lr, laikad, return_one_success=False):
  good_msgs = []
  for m in lr:
    msg = laikad.process_gnss_msg(m.ubloxGnss, m.logMonoTime, block=True)
    if msg is not None and len(msg.gnssMeasurements.correctedMeasurements) > 0:
      good_msgs.append(msg)
      if return_one_success:
        return msg
  return good_msgs


def get_first_gps_time(logs):
  for m in logs:
    if m.ubloxGnss.which == 'measurementReport':
      new_meas = read_raw_ublox(m.ubloxGnss.measurementReport)
      if len(new_meas) > 0:
        return new_meas[0].recv_time


def get_measurement_mock(gpstime, sat_ephemeris):
  meas = GNSSMeasurement(ConstellationId.GPS, 1, gpstime.week, gpstime.tow, {'C1C': 0., 'D1C': 0.}, {'C1C': 0., 'D1C': 0.})
  # Fake measurement being processed
  meas.observables_final = meas.observables
  meas.sat_ephemeris = sat_ephemeris
  return meas


GPS_TIME_PREDICTION_ORBITS_RUSSIAN_SRC = GPSTime.from_datetime(datetime(2022, month=1, day=29, hour=12))


class TestLaikad(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    logs = get_log(range(1))
    cls.logs = logs
    first_gps_time = get_first_gps_time(logs)
    cls.first_gps_time = first_gps_time

  def setUp(self):
    Params().remove(EPHEMERIS_CACHE)

  def test_fetch_orbits_non_blocking(self):
    gpstime = GPSTime.from_datetime(datetime(2021, month=3, day=1))
    laikad = Laikad()
    laikad.fetch_orbits(gpstime, block=False)
    laikad.orbit_fetch_future.result(30)
    # Get results and save orbits to laikad:
    laikad.fetch_orbits(gpstime, block=False)

    ephem = laikad.astro_dog.orbits['G01'][0]
    self.assertIsNotNone(ephem)

    laikad.fetch_orbits(gpstime+2*SECS_IN_DAY, block=False)
    laikad.orbit_fetch_future.result(30)
    # Get results and save orbits to laikad:
    laikad.fetch_orbits(gpstime + 2 * SECS_IN_DAY, block=False)

    ephem2 = laikad.astro_dog.orbits['G01'][0]
    self.assertIsNotNone(ephem)
    self.assertNotEqual(ephem, ephem2)

  def test_fetch_orbits_with_wrong_clocks(self):
    laikad = Laikad()

    def check_has_orbits():
      self.assertGreater(len(laikad.astro_dog.orbits), 0)
      ephem = laikad.astro_dog.orbits['G01'][0]
      self.assertIsNotNone(ephem)
    real_current_time = GPSTime.from_datetime(datetime(2021, month=3, day=1))
    wrong_future_clock_time = real_current_time + SECS_IN_DAY

    laikad.fetch_orbits(wrong_future_clock_time, block=True)
    check_has_orbits()
    self.assertEqual(laikad.last_fetch_orbits_t, wrong_future_clock_time)

    # Test fetching orbits with earlier time
    assert real_current_time < laikad.last_fetch_orbits_t

    laikad.astro_dog.orbits = {}
    laikad.fetch_orbits(real_current_time, block=True)
    check_has_orbits()
    self.assertEqual(laikad.last_fetch_orbits_t, real_current_time)

  def test_ephemeris_source_in_msg(self):
    data_mock = defaultdict(str)
    data_mock['sv_id'] = 1

    gpstime = GPS_TIME_PREDICTION_ORBITS_RUSSIAN_SRC
    laikad = Laikad()
    laikad.fetch_orbits(gpstime, block=True)
    meas = get_measurement_mock(gpstime, laikad.astro_dog.orbits['R01'][0])
    msg = create_measurement_msg(meas)
    self.assertEqual(msg.ephemerisSource.type.raw, EphemerisSourceType.glonassIacUltraRapid)
    # Verify gps satellite returns same source
    meas = get_measurement_mock(gpstime, laikad.astro_dog.orbits['R01'][0])
    msg = create_measurement_msg(meas)
    self.assertEqual(msg.ephemerisSource.type.raw, EphemerisSourceType.glonassIacUltraRapid)

    # Test nasa source by using older date
    gpstime = GPSTime.from_datetime(datetime(2021, month=3, day=1))
    laikad = Laikad()
    laikad.fetch_orbits(gpstime, block=True)
    meas = get_measurement_mock(gpstime, laikad.astro_dog.orbits['G01'][0])
    msg = create_measurement_msg(meas)
    self.assertEqual(msg.ephemerisSource.type.raw, EphemerisSourceType.nasaUltraRapid)

    # Test nav source type
    ephem = GPSEphemeris(data_mock, gpstime)
    meas = get_measurement_mock(gpstime, ephem)
    msg = create_measurement_msg(meas)
    self.assertEqual(msg.ephemerisSource.type.raw, EphemerisSourceType.nav)

  def test_laika_online(self):
    laikad = Laikad(auto_update=True, valid_ephem_types=EphemerisType.ULTRA_RAPID_ORBIT)
    correct_msgs = verify_messages(self.logs, laikad)

    correct_msgs_expected = 555
    self.assertEqual(correct_msgs_expected, len(correct_msgs))
    self.assertEqual(correct_msgs_expected, len([m for m in correct_msgs if m.gnssMeasurements.positionECEF.valid]))

  def test_kf_becomes_valid(self):
    laikad = Laikad(auto_update=False)
    m = self.logs[0]
    self.assertFalse(all(laikad.kf_valid(m.logMonoTime * 1e-9)))
    kf_valid = False
    for m in self.logs:
      laikad.process_gnss_msg(m.ubloxGnss, m.logMonoTime, block=True)
      kf_valid = all(laikad.kf_valid(m.logMonoTime * 1e-9))
      if kf_valid:
        break
    self.assertTrue(kf_valid)

  def test_laika_online_nav_only(self):
    laikad = Laikad(auto_update=True, valid_ephem_types=EphemerisType.NAV)
    # Disable fetch_orbits to test NAV only
    laikad.fetch_orbits = Mock()
    correct_msgs = verify_messages(self.logs, laikad)
    correct_msgs_expected = 559
    self.assertEqual(correct_msgs_expected, len(correct_msgs))
    self.assertEqual(correct_msgs_expected, len([m for m in correct_msgs if m.gnssMeasurements.positionECEF.valid]))

  @mock.patch('laika.downloader.download_and_cache_file')
  def test_laika_offline(self, downloader_mock):
    downloader_mock.side_effect = DownloadFailed("Mock download failed")
    laikad = Laikad(auto_update=False)
    laikad.fetch_orbits(GPS_TIME_PREDICTION_ORBITS_RUSSIAN_SRC, block=True)

  @mock.patch('laika.downloader.download_and_cache_file')
  def test_download_failed_russian_source(self, downloader_mock):
    downloader_mock.side_effect = DownloadFailed
    laikad = Laikad(auto_update=False)
    correct_msgs = verify_messages(self.logs, laikad)
    self.assertEqual(16, len(correct_msgs))
    self.assertEqual(16, len([m for m in correct_msgs if m.gnssMeasurements.positionECEF.valid]))

  def test_laika_get_orbits(self):
    laikad = Laikad(auto_update=False)
    # Pretend process has loaded the orbits on startup by using the time of the first gps message.
    laikad.fetch_orbits(self.first_gps_time, block=True)
    self.dict_has_values(laikad.astro_dog.orbits)

  @unittest.skip("Use to debug live data")
  def test_laika_get_orbits_now(self):
    laikad = Laikad(auto_update=False)
    laikad.fetch_orbits(GPSTime.from_datetime(datetime.utcnow()), block=True)
    prn = "G01"
    self.assertGreater(len(laikad.astro_dog.orbits[prn]), 0)
    prn = "R01"
    self.assertGreater(len(laikad.astro_dog.orbits[prn]), 0)
    print(min(laikad.astro_dog.orbits[prn], key=lambda e: e.epoch).epoch.as_datetime())

  def test_get_orbits_in_process(self):
    laikad = Laikad(auto_update=False)
    has_orbits = False
    for m in self.logs:
      laikad.process_gnss_msg(m.ubloxGnss, m.logMonoTime, block=False)
      if laikad.orbit_fetch_future is not None:
        laikad.orbit_fetch_future.result()
      vals = laikad.astro_dog.orbits.values()
      has_orbits = len(vals) > 0 and max([len(v) for v in vals]) > 0
      if has_orbits:
        break
    self.assertTrue(has_orbits)
    self.assertGreater(len(laikad.astro_dog.orbit_fetched_times._ranges), 0)
    self.assertEqual(None, laikad.orbit_fetch_future)

  def test_cache(self):
    laikad = Laikad(auto_update=True, save_ephemeris=True)

    def wait_for_cache():
      max_time = 2
      while Params().get(EPHEMERIS_CACHE) is None:
        time.sleep(0.1)
        max_time -= 0.1
        if max_time < 0:
          self.fail("Cache has not been written after 2 seconds")

    # Test cache with no ephemeris
    laikad.cache_ephemeris(t=GPSTime(0, 0))
    wait_for_cache()
    Params().remove(EPHEMERIS_CACHE)

    laikad.astro_dog.get_navs(self.first_gps_time)
    laikad.fetch_orbits(self.first_gps_time, block=True)

    # Wait for cache to save
    wait_for_cache()

    # Check both nav and orbits separate
    laikad = Laikad(auto_update=False, valid_ephem_types=EphemerisType.NAV, save_ephemeris=True)
    # Verify orbits and nav are loaded from cache
    self.dict_has_values(laikad.astro_dog.orbits)
    self.dict_has_values(laikad.astro_dog.nav)
    # Verify cache is working for only nav by running a segment
    msg = verify_messages(self.logs, laikad, return_one_success=True)
    self.assertIsNotNone(msg)

    with patch('selfdrive.locationd.laikad.get_orbit_data', return_value=None) as mock_method:
      # Verify no orbit downloads even if orbit fetch times is reset since the cache has recently been saved and we don't want to download high frequently
      laikad.astro_dog.orbit_fetched_times = TimeRangeHolder()
      laikad.fetch_orbits(self.first_gps_time, block=False)
      mock_method.assert_not_called()

      # Verify cache is working for only orbits by running a segment
      laikad = Laikad(auto_update=False, valid_ephem_types=EphemerisType.ULTRA_RAPID_ORBIT, save_ephemeris=True)
      msg = verify_messages(self.logs, laikad, return_one_success=True)
      self.assertIsNotNone(msg)
      # Verify orbit data is not downloaded
      mock_method.assert_not_called()

  def dict_has_values(self, dct):
    self.assertGreater(len(dct), 0)
    self.assertGreater(min([len(v) for v in dct.values()]), 0)


if __name__ == "__main__":
  unittest.main()
