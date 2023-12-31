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

from pcse.base.weather import WeatherDataProvider, WeatherDataContainer

from pcse.fileinput import CABOFileReader



class PandasWeatherDataProvider(WeatherDataProvider):
    def __init__(self, df, elevation=60, latitude=52, longitude=1):
        """
        Initialize the custom weather data provider with a Pandas DataFrame.

        :param df: Pandas DataFrame containing weather data.
        """
        WeatherDataProvider.__init__(self)
        self.elevation = elevation
        self.latitude = latitude
        self.longitude = longitude
        self._last_date  = np.max(df["day"])
        self._first_date = np.min(df["day"])

        self.df = df
        print(self.df)

    def __call__(self, day, member_id=0):        
        entry = self.df[self.df.day == day]

        if len(entry) == 0: return None

        entry = entry.iloc[0]

        sitevar = ["LAT", "LON", "ELEV"]
        required = ["IRRAD", "TMIN", "TMAX", "VAP", "RAIN", "E0", "ES0", "ET0", "WIND"]
        optional = ["SNOWDEPTH", "TEMP", "TMINRA"]
        
        wdc = {}
        
        for key in sitevar + required + optional:
            wdc[key] = 0.0
        
        wdc["TMINRA"] = float(entry["airtemperature"])
        wdc["LAT"] = self.latitude
        wdc["LON"] = self.longitude
        wdc["ELEV"] = self.elevation
        wdc["DAY"] = day
        wdc["IRRAD"] = float(entry["solarradiation"])
        wdc["TMIN"] = float(entry["airtemperature"])
        wdc["TMAX"] = float(entry["airtemperature"])
        wdc["VAP"] = float(entry["airpressure"])/8
        wdc["RAIN"] = float(entry["rainfall"])
        wdc["WIND"] = float(entry["windspeed"])
        wdc["E0"] = 1.0
        wdc["ES0"] = 1.0
        wdc["ET0"] = 1.0
        wdc["TEMP"] = float(entry["airtemperature"])
        wdc["SNOWDEPTH"] = 0.0

        wdc_date = WeatherDataContainer(**wdc)

        return wdc_date




field_center = [-45.523917847717236,-12.170341419421398]

def get_daily_date(session, entity_id, timestartstr, timeendstr, keys):

    weather_data = cosmicswamp.get_series_data_for_entity(session, entity_id, attrs=["time_index, *"], limit=1000, cuts=[f"time_index BETWEEN '{timestartstr}' AND '{timeendstr}'"])
    data = pd.DataFrame(data=(weather_data))
    print(weather_data)
    try:
        daily_data = data[keys]
        daily_data = daily_data.mean()
        return daily_data
    except:
        return pd.DataFrame({})

def get_mean_daily_data_for_all(session, entity_list, time_start, keys):
    time_end   = time_start - datetime.timedelta(hours=480)
    timestartstr = time_end.isoformat()
    timeendstr   = time_start.isoformat()

    if len(entity_list) == 0: return pd.DataFrame({})
    keys.append("time_index")
    df = None
    for i, e in enumerate(entity_list):
        temp_df = get_daily_date(session, e["id"], timestartstr, timeendstr, keys)
        if i == 0: df = temp_df
        else: df = pd.concat([df,temp_df])

    return df.mean()

def simulate_zone(zone, time_start):

    zoneid = zone["zoneid"]["value"]
    zone_location = zone["location"]["value"]

    # Get Crop data for zone
    pos_search = geojson.to_wgs84_list(zone_location["coordinates"])
    mean_pos = geojson.mean_lon_lat_from_polygon(zone["location"])

    point_search = geojson.to_wgs84_list([[[mean_pos[0], mean_pos[1]]]])

    agros = cosmicswamp.get_entities_by_type_and_geometry(session, "Agronomy", pos_search)
    crops = cosmicswamp.get_entities_by_type_and_geometry(session, "Crop", pos_search)
    soils = cosmicswamp.get_entities_by_type_and_geometry(session, "Soil", pos_search)
    soildepthprobes = cosmicswamp.get_entities_by_type_and_geometry(session, "SoilDepthProbe", pos_search)
    neutronprobe = cosmicswamp.get_entities_by_type_and_geometry(session, "NeutronProbe", pos_search)

    avg_agro = ngsi.mean(agros)
    avg_crop = ngsi.mean(crops)
    avg_soil = ngsi.mean(soils)

    wstations = cosmicswamp.get_all_current_entities_of_type(session, "WeatherStation")
    # wstations = cosmicswamp.get_entities_by_type_and_geometry(session, "WeatherStation", point_search, maxDistance=1000)
    print(wstations)
    wstationid = wstations[0]["id"]
    
    dfw = get_mean_daily_data_for_all(session, wstations, time_start, ["airtemperature","airpressure","airhumidity","windspeed","winddirection","solarradiation","rainfall"])
    dfs = get_mean_daily_data_for_all(session, soildepthprobes, time_start, ["soilmoisturecalibrated0","soilmoisturecalibrated1","soilmoisturecalibrated2"])
    dfn = get_mean_daily_data_for_all(session, neutronprobe, time_start, ["soilmoisturecentral"])


    print("ENTITY")
    print("DFW", dfw)
    print("DFs", dfs)
    print("DFn", dfn)


    

    


import concurrent.futures

time_start = pd.to_datetime("2023-04-13T23:48:06")


zones = information_platform.field.get_associated_zones(session, "Field:1")
for z in zones:
    simulate_zone(z, time_start)

# with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
#     executor.map(simulate_zone, zones)

# The ThreadPool will automatically manage the execution of the function in parallel