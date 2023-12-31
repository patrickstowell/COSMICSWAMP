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

def to_unix(dt):
    return float(time.mktime(dt.timetuple()))


start_date="2023-01-01"
end_date="2028-05-01"

time_high = to_unix(pd.to_datetime(start_date))
time_low = to_unix(pd.to_datetime(end_date))


print("WEATHER FUSION CHECK")
weather_data = cosmicswamp.get_series_data_for_entity(session, "urn:ngsi-ld:WeatherStation:1", attrs=["time_index","airtemperature","airpressure","airhumidity","windspeed","winddirection","solarradiation","batteryvoltage","rainfall"], limit=100000)
weather_df = []
if len(weather_data) > 0:
    data = pd.DataFrame(data=(weather_data))

    # Merge data to get average per day
    data["date"] = pd.to_datetime(data["time_index"], unit="ms")
    data["day"]  = data["date"].dt.date
    hourly_data = data[["day","airtemperature","airpressure","airhumidity","windspeed","winddirection","solarradiation","batteryvoltage","rainfall"]]
    daily_data = hourly_data.groupby("day").mean().reset_index()
    
    daily_data['day'] = daily_data['day'].map(lambda x: x.isoformat())
    weather_df = daily_data


print(weather_df)


longitude, latiude = [-45.523917847717236,-12.170341419421398]
weather_df["TEMP"] = weather_df["airtemperature"]
weather_df["TMIN"] = weather_df["airtemperature"]
weather_df["TMAX"] = weather_df["airtemperature"]

print(weather_df)

# averaged_weather_provider = PandasWeatherDataProviderForecastingModel(weather_df, longitude=longitude, latitude=latiude)
averaged_weather_provider = information_platform.weatherstation.PandasWeatherDataProvider(weather_df, elevation=60, longitude=longitude, latitude=latiude)


pre_date = (pd.to_datetime(start_date)).date()
end_date = pd.to_datetime(end_date).date()
dataset = {
    "Date":   [],
    "IRRAD": [],
    "TMIN":  []
}

count = 0
while pre_date < end_date:
    print(pre_date)
    pre_date += datetime.timedelta(days=1)
    count += 1

    row =   averaged_weather_provider(pre_date)
    print(count, row)
    dataset["Date"].append(pre_date)
    dataset["IRRAD"].append(row.IRRAD)
    dataset["TMIN"].append(row.TMIN)

print(dataset)
df = pd.DataFrame(data=dataset)
print(df)
plt.plot(df.Date,df.IRRAD)
plt.show()




          

    
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
