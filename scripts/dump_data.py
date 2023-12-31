from fastapi import FastAPI, Request
import dependencies.orion_utils as orion
import dependencies.geojson_utils as geojson
import dependencies.ngsi_utils as ngsi
import paho.mqtt.client as Paho
import matplotlib.pyplot as plt
import scipy
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.simulation_platform.pcse_simulator as pcse_simulator
import modules.information_platform as information_platform
import modules.iot_platform as iot_platform
import sys
import time

import datetime
import time
from pcse.db import NASAPowerWeatherDataProvider
import yaml
import pcse
import pcse
from pcse.models import Wofost72_WLP_FD
from pcse.fileinput import CABOFileReader, YAMLCropDataProvider
from pcse.db import NASAPowerWeatherDataProvider
from pcse.util import WOFOST72SiteDataProvider
from pcse.base import ParameterProvider
import numpy as np
import pandas as pd

session = orion.session(servicepath="/test_process")


sensor_data = pd.DataFrame(data=cosmicswamp.get_series_data_for_entity(session, "urn:ngsi-ld:SoilProbe:F1-0-0", limit=1000000,
    attrs=["time_index", "soilmoistureraw0","soilmoisturecalibrated0","soilmoistureraw1","soilmoisturecalibrated1", "soilmoistureraw2", "soilmoisturecalibrated2"]))


print(sensor_data)
sensor_data["date"] = pd.to_datetime(sensor_data["time_index"], unit='ms')


data2000 = pd.DataFrame(data=cosmicswamp.get_series_data_for_entity(session, "urn:ngsi-ld:NeutronProbe:Dry2000", limit=1000000,
    attrs=["time_index", "soilmoisturecentral","neutroncountsraw"]))
data1500 = pd.DataFrame(data=cosmicswamp.get_series_data_for_entity(session, "urn:ngsi-ld:NeutronProbe:Dry1500", limit=1000000,
    attrs=["time_index", "soilmoisturecentral","neutroncountsraw"]))
data1000 = pd.DataFrame(data=cosmicswamp.get_series_data_for_entity(session, "urn:ngsi-ld:NeutronProbe:Dry1000", limit=1000000,
    attrs=["time_index", "soilmoisturecentral","neutroncountsraw"]))

data2000["date"] = pd.to_datetime(data2000["time_index"], unit='ms')
data1500["date"] = pd.to_datetime(data1500["time_index"], unit='ms')
data1000["date"] = pd.to_datetime(data1000["time_index"], unit='ms')

# Get Time Series Weather Data
weather_data = cosmicswamp.get_series_data_for_entity(session, "WeatherStation:1", attrs=["*"], limit=1000000)
data = pd.DataFrame(data=(weather_data))

# Merge data to get average per day
data["date"] = pd.to_datetime(data["time_index"], unit="ms")
data["day"]  = data["date"].dt.date
daily_data = data[["day","airtemperature","airpressure","airhumidity","windspeed","winddirection","solarradiation","batteryvoltage","rainfall"]]
daily_data = daily_data.groupby("day").mean().reset_index()
daily_data["date"] = pd.to_datetime(daily_data["day"])

# plt.plot(data1000.date, np.sqrt(data1000.neutroncountsraw)/data1000.neutroncountsraw)
# # plt.plot(data.date, np.sqrt(data1500.neutroncountsraw)/data1500.neutroncountsraw)
# # plt.plot(data.date, np.sqrt(data2000.neutroncountsraw)/data2000.neutroncountsraw)
# plt.show()


fig, (ax1, ax2) = plt.subplots(2)

# ax1.plot(daily_data.date, daily_data.rainfall*0.5/np.max(daily_data.rainfall), c='lightgray')
ax1.fill_between(daily_data.date, daily_data.rainfall*0.3/np.max(daily_data.rainfall), color='lightgray')
ax1.plot(sensor_data.date, sensor_data.soilmoisturecalibrated0, label="Simulated Depth Probe - 10cm")
ax1.plot(sensor_data.date, sensor_data.soilmoisturecalibrated1, label="Simulated Depth Probe - 25cm")
ax1.plot(sensor_data.date, sensor_data.soilmoisturecalibrated2, label="Simulated Depth Probe - 40cm")
ax1.set_xlim([np.min(sensor_data.date), np.max(sensor_data.date)])
ax1.set_ylim([0.0,0.5])
ax1.set_ylabel("SM Estimate [%]")
ax1.legend()

# ax2.plot(daily_data.date, daily_data.rainfall*0.5/np.max(daily_data.rainfall), c='lightgray', label="Rainfall [arb.]")
ax2.fill_between(daily_data.date, daily_data.rainfall*0.3/np.max(daily_data.rainfall), color='lightgray', label="Rainfall [arb.]")
ax2.scatter(data1000.date, data1000.soilmoisturecentral, s=4, label="Simulated Neutron Probe")
ax2.set_xlim([np.min(sensor_data.date), np.max(sensor_data.date)])
ax2.set_ylim([0.0,0.5])

ax2.set_xlabel("Date")
ax2.set_ylabel("SM Estimate [%]")
ax2.legend()

for date0 in [datetime.datetime(2023,9,1), datetime.datetime(2023,9,15), datetime.datetime(2023,10,1), datetime.datetime(2023,10,15)]:
    ax1.plot([date0, date0], [0.0, 0.5], color='blue', linestyle='-', linewidth=2)
    ax2.plot([date0, date0], [0.0, 0.5], color='blue', linestyle='-', linewidth=2)

plt.show()
