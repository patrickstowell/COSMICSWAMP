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

time_start = pd.to_datetime("2023-08-13T23:48:06")

field_center = [-45.523917847717236,-12.170341419421398]

for e in cosmicswamp.get_all_current_entities_of_type(session, "CalibrationMeasurement"):
    cosmicswamp.delete_entity(session, e["id"], purge=True)
    cosmicswamp.delete_timeseries_for_entity(session, e["id"], e["type"])

for i in range(100):
    location = geojson.point( [field_center[0] + np.random.normal(0.0,0.001), field_center[1] + np.random.normal(0.0,0.001)] )
    print(i,location)

    information_platform.calibrationmeasurement.create(session, "ECMap:Run1", time_start, location, index=i, type="Number", label="Run1", number=np.random.normal(0.0,1.0))