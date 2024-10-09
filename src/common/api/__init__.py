import os
import logging
import json

from system.swaglog import cloudlog
from common.params import Params

import urllib3

logger = logging.getLogger(__name__)

API_HOST = os.getenv('API_HOST', 'https://staging-api.flowdrive.ai')

class Api():
  def __init__(self):
    self.params = Params()
    self.http_client = urllib3.PoolManager()

  def get_credentials(self):
    # Get auth token
    self.user_id = self.params.get("UserID").decode()
    self.token = self.params.get("UserToken").decode()
    self.dongle_id = self.params.get("DongleId")
    if self.dongle_id is None:
      self.dongle_id = b"f"*16
    self.dongle_id = self.dongle_id.decode()

    if self.token is None:
      logger.error(f"Error retrieving auth token")
    
    logger.debug(f"Fetched auth token ***")

    # Get STS
    r = self.http_client.request(
        'GET',
        f"{API_HOST}/auth/sts",
        headers={'Authorization': f"Bearer {self.token}"}
    )
    cloudlog.info("api init statuscode %d", r.status)

    r_data = json.loads(r.data.decode('utf-8'))
    if r_data["success"] == True:
      return r_data["message"]
    else:
      raise Exception(f"Fetching token from STS endpoint unsuccessful: {r_data['message']}")
