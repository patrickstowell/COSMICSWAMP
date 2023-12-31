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

import scipy

import numpy as np
import pandas as pd

session = orion.session(servicepath="/test_process")

cosmicswamp.delete_timeseries_for_entity(session, "WeatherStation:1", "WeatherStation")

location = [-1.4856405914957844, 51.53370349911278]
information_platform.weatherstation.create(session, "WeatherStation:1", location=geojson.point([location[0], location[1]]))

time_start = pd.to_datetime("2022-05-13T23:48:06")
time_end = pd.to_datetime("2023-11-28")
time_step  = datetime.timedelta(hours=1)
time_wind  = datetime.timedelta(hours=12)

longitude, latiude = location

weatherdata = NASAPowerWeatherDataProvider(longitude=longitude, latitude=latiude)
dataset = []
while time_start < time_end:
  t0 = (time_start)
  print(t0)
  vals0 = weatherdata(t0)

  data0 = {}
  data0["DAY"] = t0
  data0["IRRAD"] = vals0.IRRAD
  data0["TMIN"] = vals0.TMIN
  data0["TMAX"] = vals0.TMAX
  data0["VAP"] = vals0.VAP
  data0["RAIN"] = vals0.RAIN
  data0["E0"] = vals0.ES0
  data0["E0"] = vals0.ES0
  data0["ES0"] = vals0.ES0
  data0["ET0"] = vals0.ET0
  data0["WIND"] = vals0.WIND
  data0["TEMP"] = vals0.TEMP
  data0["ELEV"] = vals0.ELEV

  dataset.append(data0)
  time_start += time_wind



weatherdf = pd.DataFrame(data=dataset)
weatherdf["UNIX"] = weatherdf["DAY"].astype(int) / 10**9

time_start = np.min(weatherdf.DAY)
time_end   = np.max(weatherdf.DAY)
time_step  = datetime.timedelta(hours=1)

time_array = []
date_array = []
while time_start < time_end:
  time_array.append((pd.to_datetime([time_start]).astype(int) / 10**9)[0])
  time_start += time_step
time_array = np.array(time_array)

data_lists = {}
data_lists["DAY"] = pd.to_datetime(time_array, unit='s')
data_lists["UNIX"] = time_array

for key in weatherdf:
    if key == "UNIX": continue
    if key == "DAY": continue
    func = scipy.interpolate.interp1d( weatherdf["UNIX"], weatherdf[key] )
    print(key)
    data_lists[key] = func(time_array)

    print(key, len(data_lists[key]))
print("DATALIST", data_lists)
finaldf = pd.DataFrame(data=data_lists)
print("FINALDF", finaldf)
import matplotlib.pyplot as plt

  
count = 0
for i in range(len(finaldf)) :
  entry = finaldf.iloc[i]
  information_platform.weatherstation.update_from_pcse_wdp( session, "WeatherStation:1", entry, entry["DAY"] )
  count += 1

  if count % 24 == 0:
    print(count, entry)
  # time.sleep(0.1)
  


# Create soil, crop, sorghume
# Create probs in every zone


