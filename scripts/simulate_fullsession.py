from fastapi import FastAPI, Request
import dependencies.orion_utils as orion
import dependencies.geojson_utils as geojson
import dependencies.ngsi_utils as ngsi
import paho.mqtt.client as Paho
import matplotlib.pyplot as plt
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.simulation_platform.pcse_simulator as pcse_simulator
import modules.information_platform as information_platform
import modules.iot_platform as iot_platform
import modules.fusion_platform as fusion_platform

import sys
import datetime
import time


import datetime
import time
from pcse.db import NASAPowerWeatherDataProvider
import yaml
import pcse
from pcse.models import Wofost72_WLP_FD
from pcse.fileinput import CABOFileReader, YAMLCropDataProvider
from pcse.db import NASAPowerWeatherDataProvider
from pcse.util import WOFOST72SiteDataProvider
from pcse.base import ParameterProvider


import numpy as np
import pandas as pd

import numpy as np

simulation_name = "/new_session"
simulation_refresh = True

#########################
# SESSION CREATION STAGE
#########################
session = orion.session(servicepath=simulation_name)

################################
# FIELD SOIL MOISTURE SIMULATION
################################
field_loc = cosmicswamp.get_current_entity_from_id(session, "Field:1")["location"]["value"]
agros = cosmicswamp.get_entities_by_type_and_geometry(session, "Agronomy", geojson.to_wgs84_list(field_loc["coordinates"]))

# Determine start oof growing period
start_time = None
end_time = None
for ag in agros:
  st = pd.to_datetime(ag["start_date"]["value"])
  if not start_time or st < start_time: start_time = st

  et = pd.to_datetime(ag["end_date"]["value"])
  if not end_time or et < end_time: end_time = et

# Simulate a stack for every managementzone
zone_simulations = {}
for zone in information_platform.field.get_associated_zones(session, "Field:1"):

  zoneid = zone["zoneid"]["value"]
  zone_location = zone["location"]["value"]

  # Get Crop data for zone as this may not change
  agros = cosmicswamp.get_entities_by_type_and_geometry(session, "Agronomy", geojson.to_wgs84_list(zone_location["coordinates"]))
  crops = cosmicswamp.get_entities_by_type_and_geometry(session, "Crop", geojson.to_wgs84_list(zone_location["coordinates"]))
  soils = cosmicswamp.get_entities_by_type_and_geometry(session, "Soil", geojson.to_wgs84_list(zone_location["coordinates"]))

  avg_agro = ngsi.mean(agros)
  avg_crop = ngsi.mean(crops)
  avg_soil = ngsi.mean(soils)

  # Build wofost handlers
  agro_provider = information_platform.agronomy.pcse_agro_from_ngsi(avg_agro)
  soil_provider = information_platform.soil.pcse_soil_from_ngsi(avg_soil)  
  site_provider = WOFOST72SiteDataProvider(WAV=20, SSMAX=1)
  crop_provider = YAMLCropDataProvider(fpath="data/WOFOST_crop_parameters/")

  parameter_provider = ParameterProvider(soildata=soil_provider,
                                          cropdata=crop_provider,
                                          sitedata=site_provider)
  
  # Build WDP Interpolator
  longitude, latiude = geojson.mean_lon_lat_from_polygon(zone["location"])
  truth_weather_provider = NASAPowerWeatherDataProvider(longitude=longitude, latitude=latiude)

  # Run WOFOST end to end
  wofost = Wofost72_WLP_FD(parameter_provider, truth_weather_provider, agro_provider)
  wofost.run_till_terminate()

  df = pd.DataFrame(wofost.get_output())
  df["day"] = pd.to_datetime(df.day)
  df["unix"] = df["day"].astype(int) / 10**9

  zone_simulations[zone["id"]] = df
  

# START SIMULATION
count = 0
while start_time < end_time:
  start_time += datetime.timedelta(hours=1)
  count += 1

  print(start_time)

  # Simulate weather data
  wdp_row  = information_platform.weatherstation.interpolate_pcse_wdp_to_ngsi(truth_weather_provider, start_time)
  information_platform.weatherstation.update(session, "WeatherStation:1", jsondata=wdp_row, time_index=start_time)

  # Simulate all probes on platform
  for probe in cosmicswamp.get_all_current_entities_of_type(session, "SoilDepthProbe"):

    zones = cosmicswamp.get_entities_by_type_and_geometry(session, "ManagementZone", geojson.to_wgs84_list(probe["location"]["value"]["coordinates"]))

    mean_sm = 0.0
    count_sm = 0.0
    for zone in zones:
      entity_id = zone["id"]
      zone_simulations[entity_id]["date"] = zone_simulations[entity_id]["day"]
      sm_interp = ngsi.interpolate_df(zone_simulations[entity_id], start_time, "SM")
      mean_sm += sm_interp
      count_sm += 1.0

    probe_id = probe["id"]

    sm0_estimate = mean_sm / count_sm
    sm1_estimate = mean_sm / count_sm
    sm2_estimate = mean_sm / count_sm

    information_platform.soildepthprobe.simulate(session, 
                                                probe_id, 
                                                time_index=start_time.isoformat(), 
                                                soilmoistureraw0=sm0_estimate,
                                                soilmoistureraw1=sm1_estimate,
                                                soilmoistureraw2=sm2_estimate
                                                )
    
  # COSMIC DATA REQUEST
    
  # Simulate all probes on platform
  for probe in cosmicswamp.get_all_current_entities_of_type(session, "NeutronProbe"):

    zones = cosmicswamp.get_entities_by_type_and_geometry(session, "ManagementZone", geojson.to_wgs84_list(probe["location"]["value"]["coordinates"]))

    mean_sm = 0.0
    count_sm = 0.0
    for zone in zones:
      entity_id = zone["id"]
      zone_simulations[entity_id]["date"] = zone_simulations[entity_id]["day"]
      sm_interp = ngsi.interpolate_df(zone_simulations[entity_id], start_time, "SM")
      mean_sm += sm_interp
      count_sm += 1.0

    probe_id = probe["id"]

    sm0_estimate = mean_sm / count_sm
    sm1_estimate = mean_sm / count_sm
    sm2_estimate = mean_sm / count_sm

    information_platform.neutronprobe.simulate(session, probe_id,
                                                time_index=start_time.isoformat(), 
                                                smc0=sm0_estimate,
                                                nd0=2000)
    
  if count % 24 == 0:
    print("PROCESSING DAILY MIGRATIONS")
    fusion_platform.zone_fusion.process_all_zones_in_platform(start_time, start_time - datetime.timedelta(hours=24))


# UPDATE {'data': [{'TimeInstant': {'value': '2023-01-02T00:00:00+00:00', 'type': 'DateTime'}, 'location': {'type': 'geo:json', 'value': {'type': 'Polygon', 'coordinates': [[[-45.523918, -12.170341], [-45.523918, -12.168542], [-45.525512, -12.17124], [-45.523918, -12.170341], [-45.523918, -12.170341]]]}, 'metadata': {}}, 'test': {'type': 'Number', 'value': 1, 'metadata': {}}, 'zoneid': {'type': 'String', 'value': '0-0', 'metadata': {}}, 'id': 'urn:ngsi-ld:Field:1:ManagementZone:0-0', 'type': 'ManagementZone'}], 'subscriptionId': '654db53240157754c3d09cdf'}
# UPDATE {'data': [{'TimeInstant': {'value': '2023-01-14T00:00:00+00:00', 'type': 'DateTime'}, 'test': {'type': 'Number', 'value': 1.0, 'metadata': {}}, 'id': 'urn:ngsi-ld:Field:1:ManagementZone:0-0', 'type': 'ManagementZone'}], 'subscriptionId': '654db53240157754c3d09cdf'}


# for k in zone_simulations: 
  
#   print(k, zone_simulations[k])
#   plt.plot( zone_simulations[k].day, zone_simulations[k].SM )
#   plt.show()

#   while start_time < end_time:
#     start_time += time_step

#   ngsi.interpolate_df_from_datetime(zone_simulations[k], "SM", time_index)

#   zone = cosmicswamp.get_current_entity_from_id(session, k)

#   zoneid = zone["zoneid"]["value"]
#   zone_location = zone["location"]["value"]

#   # Get Crop data for zone as this may not change
#   agros = cosmicswamp.get_entities_by_type_and_geometry(session, "Agronomy", geojson.to_wgs84_list(zone_location["coordinates"]))
#   crops = cosmicswamp.get_entities_by_type_and_geometry(session, "Crop", geojson.to_wgs84_list(zone_location["coordinates"]))
#   soils = cosmicswamp.get_entities_by_type_and_geometry(session, "Soil", geojson.to_wgs84_list(zone_location["coordinates"]))



# count = 0
# time_step  = datetime.timedelta(hours=1)
# while start_time < end_time:
#   count += 1
#   start_time += time_step

  

#     # WDP Iterator
#     count = 0
#     while time_start < time_end:
#       count += 1
#       time_start += time_step

#       # First simulate the weather
#       wdp_row  = information_platform.weatherstation.interpolate_pcse_wdp_to_ngsi(truth_weather_provider, time_start)
#       information_platform.weatherstation.update(session, "WeatherStation:1", jsondata=wdp_row, time_index=time_start)

#       # Every 24 hurs of uploads we run the daily forecasting
#       if count % 24 == 0: 
#         print(time_start)


      




# dataset = []
# while time_start < time_end:
#   t0 = (time_start)
#   print(t0)
#   vals0 = weatherdata(t0)

#   data0 = {}
#   data0["DAY"] = t0
#   data0["IRRAD"] = vals0.IRRAD
#   data0["TMIN"] = vals0.TMIN
#   data0["TMAX"] = vals0.TMAX
#   data0["VAP"] = vals0.VAP
#   data0["RAIN"] = vals0.RAIN
#   data0["E0"] = vals0.ES0
#   data0["E0"] = vals0.ES0
#   data0["ES0"] = vals0.ES0
#   data0["ET0"] = vals0.ET0
#   data0["WIND"] = vals0.WIND
#   data0["TEMP"] = vals0.TEMP
#   data0["ELEV"] = vals0.ELEV

#   dataset.append(data0)
#   time_start += time_wind

#   weatherdf = pd.DataFrame(data=dataset)
#   weatherdf["UNIX"] = weatherdf["DAY"].astype(int) / 10**9

#   time_start = np.min(weatherdf.DAY)
#   time_end   = np.max(weatherdf.DAY)
#   time_step  = datetime.timedelta(hours=1)

#   time_array = []
#   date_array = []
#   while time_start < time_end:
#     time_array.append((pd.to_datetime([time_start]).astype(int) / 10**9)[0])
#     time_start += time_step
#   time_array = np.array(time_array)

#   data_lists = {}
#   data_lists["DAY"] = pd.to_datetime(time_array, unit='s')
#   data_lists["UNIX"] = time_array

#   for key in weatherdf:
#       if key == "UNIX": continue
#       if key == "DAY": continue
#       func = scipy.interpolate.interp1d( weatherdf["UNIX"], weatherdf[key] )
#       print(key)
#       data_lists[key] = func(time_array)

#       print(key, len(data_lists[key]))
#   print("DATALIST", data_lists)
#   finaldf = pd.DataFrame(data=data_lists)
#   print("FINALDF", finaldf)
#   import matplotlib.pyplot as plt

    
#   count = 0
#   for i in range(len(finaldf)) :
#     entry = finaldf.iloc[i]
#     information_platform.weatherstation.update_from_pcse_wdp( session, "WeatherStation:1", entry, entry["DAY"] )
#     count += 1

#     if count % 24 == 0:
#       print(count, entry)




#     weather_provider = information_platform.weatherstation.build_wdp_from_weatherstation(session, "WeatherStation:1")
#     agro_provider = information_platform.agronomy.pcse_agro_from_ngsi(avg_agro)
#     soil_provider = information_platform.soil.pcse_soil_from_ngsi(avg_soil)  
#     site_provider = WOFOST72SiteDataProvider(WAV=20, SSMAX=1)
#     crop_provider = YAMLCropDataProvider(fpath="WOFOST_crop_parameters/")

#     parameter_provider = ParameterProvider(soildata=soil_provider,
#                                             cropdata=crop_provider,
#                                             sitedata=site_provider)

#     print("Sttarting WOFOST")
#     wofost = Wofost72_WLP_FD(parameter_provider, weather_provider, agro_provider)
#     wofost.run_till_terminate()

#     df = pd.DataFrame(wofost.get_output())
#     df["day"] = pd.to_datetime(df.day)
#     df["unix"] = df["day"].astype(int) / 10**9

#     print(df)

#     time_start = np.min(df.day)
#     time_end   = np.max(df.day)
#     time_step  = datetime.timedelta(hours=1)
#     time_current = time_start
#     func = scipy.interpolate.interp1d(df.unix, df.SM) 
