from fastapi import FastAPI, Request
import dependencies.orion_utils as orion
import dependencies.geojson_utils as geojson
import dependencies.ngsi_utils as ngsi
import paho.mqtt.client as Paho

import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.simulation_platform.pcse_simulator as pcse_simulator
import modules.information_platform as information_platform
import modules.iot_platform as iot_platform
import sys
import datetime
import time
from pcse.db import NASAPowerWeatherDataProvider

import numpy as np
import pandas as pd

session = orion.session(servicepath="/test_process")

print("SESSION",cosmicswamp.get_current_entity_from_id(session, "Field:1") )
location = (cosmicswamp.get_current_entity_from_id(session, "Field:1")["location"])

time_start = pd.to_datetime("2023-09-13T23:48:06")
time_end   = pd.to_datetime("2023-12-13T23:48:06")

# information_platform.crop.create(session, "Crop:1", location=location,
#                                 time_index=time_start.isoformat(),
#                                 start_date=time_start.isoformat(),
#                                 base="sorghum.yaml",
#                                 crop_name=""
#                                 end_date=time_end.isoformat(),
#                                 start_type="emergence",
#                                 end_type="harvest",
#                                 max_duration=300,
#                                 crop_name="sorgohme",
#                                 variety_name="Sorghum_VanHeemst_1988")
