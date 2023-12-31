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

time_start = pd.to_datetime("2023-09-13T23:48:06")
time_end   = pd.to_datetime("2023-11-13T23:48:06")

neutron_locations = [
    [-45.520420338247504, -12.17053767225633],
    [-45.52433973726252,  -12.173866100484176],
    [-45.52389880487357,  -12.170346106772087],
    [-45.52566253443007,  -12.168143093782376]
]

for i, pos in enumerate(neutron_locations):
    information_platform.neutron_probe.create(session, f"NeutronProbe:{i}", center_location=(pos), radius=200)
