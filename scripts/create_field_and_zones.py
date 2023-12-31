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

import numpy as np

session = orion.session(servicepath="/test_process")

# if (cosmicswamp.has_session(session)):
  # cosmicswamp.delete_session(session, purge=True)

# cosmicswamp.register_session(session)

field_center = [-45.523917847717236,-12.170341419421398]
information_platform.field.create(session, "Field:1", center_location=field_center, radius=600)
information_platform.field.split_into_radial_zones(session, "Field:1", nradial=4, naround=12)

for zone in information_platform.field.get_associated_zones(session, "Field:1"):

  zoneid = zone["zoneid"]["value"]

  lat,lon = geojson.split_lat_lon_from_polygon(zone["location"]["value"])
  
  centrelat = np.mean(lat)
  centrelon = np.mean(lon)

  information_platform.soildepthprobe.create(session, f"SoilProbe:F1-{zoneid}", location=geojson.point([centrelon,centrelat]))