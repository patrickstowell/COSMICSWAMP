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

simulation_name = "/new_session"
simulation_refresh = True

#########################
# SESSION CREATION STAGE
#########################
cosmicswamp.create_root_session_map()

session = orion.session(servicepath=simulation_name)

if (cosmicswamp.has_session(session) and simulation_refresh):
  cosmicswamp.delete_session(session, purge=True)

if (not cosmicswamp.has_session(session)):
  cosmicswamp.register_session(session)

#########################
# FIELD CREATION
#########################
field_center = [-45.523917847717236,-12.170341419421398]
information_platform.field.create(session, "Field:1", center_location=field_center, radius=600)
information_platform.field.split_into_radial_zones(session, "Field:1", nradial=3, naround=3)

#########################
# DEPTH PROBE CREATION
#########################
for zone in information_platform.field.get_associated_zones(session, "Field:1"):
  zoneid = zone["zoneid"]["value"]
  zoneloc = zone["location"]["value"]

  information_platform.soildepthprobe.create(session, 
                                            f"SoilProbe:F1-{zoneid}", 
                                            location=geojson.center_point_of_polygon(zoneloc))
  
#########################
# NEUTRON PROBE CREATION
#########################
for zone in information_platform.field.get_associated_zones(session, "Field:1"):
  zoneid = zone["zoneid"]["value"]
  
  # Only middle radial and every other zone
  if "-1" not in zoneid: continue
  if int(zoneid.split("-")[0]) % 2 != 0: continue
  
  zoneloc = zone["location"]["value"]
  print("LOCATION : ", geojson.center_point_of_polygon(zoneloc))
  information_platform.neutronprobe.create(session, 
                                            f"NeutronProbe:F1-{zoneid}", 
                                            location=geojson.center_point_of_polygon(zoneloc))
    
#########################
# WEATHER CREATION
#########################
fieldloc = cosmicswamp.get_current_entity_from_id(session, "Field:1")["location"]
information_platform.weatherstation.create(session, "WeatherStation:1", location=geojson.center_point_of_polygon(fieldloc))
information_platform.weatherforecast.create(session, "WeatherForecast:1", apitype="AccuWeather", apikey="cGimzB5H9KpGs6VMmUfpYpGryw2A4ire", location=geojson.center_point_of_polygon(fieldloc))
information_platform.weatherforecast.create(session, "WeatherForecast:2", apitype="OpenWeather", apikey="04e21480b3300453abd7d2c22477c9f7", location=geojson.center_point_of_polygon(fieldloc))
information_platform.weatherforecast.refresh_event()

#########################
# COSMIC FLUX STATION
#########################
information_platform.cosmicfluxstation.create(session, "CosmicFluxStation:1", location=geojson.center_point_of_polygon(fieldloc), nmdbstation="JUNG", nmdbbaseline=145)

#########################
# SOIL CREATION
#########################
information_platform.soil.create(session, "Soil:1", location=fieldloc)

#########################
# AGRO CREATION
#########################
start_date="2023-01-01"
end_date="2023-05-01"
information_platform.agronomy.create(session, 
                                    "Agronomy:1", 
                                    location=fieldloc, 
                                    start_date=start_date, end_date=end_date, 
                                    crop_name="barley", 
                                    variety_name="Spring_barley_301")

#########################
# Final printout
#########################
for e in (cosmicswamp.get_all_current_entity_ids(session)):
  print(e["id"])

