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




time_start = pd.to_datetime("2023-09-13T23:48:06")

field_center = [-45.523917847717236,-12.170341419421398]

def simulate_zone(zone):

    zoneid = zone["zoneid"]["value"]
    zone_location = zone["location"]["value"]

    # Get Crop data for zone
    agros = cosmicswamp.get_entities_by_type_and_geometry(session, "Agronomy", geojson.to_wgs84_list(zone_location["coordinates"]))
    crops = cosmicswamp.get_entities_by_type_and_geometry(session, "Crop", geojson.to_wgs84_list(zone_location["coordinates"]))
    soils = cosmicswamp.get_entities_by_type_and_geometry(session, "Soil", geojson.to_wgs84_list(zone_location["coordinates"]))
    
    avg_agro = ngsi.mean(agros)
    avg_crop = ngsi.mean(crops)
    avg_soil = ngsi.mean(soils)

    print("ZONE SOILS:", zoneid, len(soils), avg_soil["baseSoil"]["value"])

    # Get Time Series Weather Data
    weather_data = cosmicswamp.get_series_data_for_entity(session, "WeatherStation:1", attrs=["*"], limit=1000000)
    data = pd.DataFrame(data=(weather_data))

    # Merge data to get average per day
    data["date"] = pd.to_datetime(data["time_index"], unit="ms")
    data["day"]  = data["date"].dt.date
    daily_data = data[["day","airtemperature","airpressure","airhumidity","windspeed","winddirection","solarradiation","batteryvoltage","rainfall"]]
    daily_data = daily_data.groupby("day").mean().reset_index()
    daily_data["date"] = pd.to_datetime(daily_data["day"])

    # Setup PCSE crpo information
    weather_provider = PandasWeatherDataProvider(daily_data)

    # Convert to providers
    agro_provider = information_platform.agronomy.pcse_agro_from_ngsi(avg_agro)
    soil_provider = information_platform.soil.pcse_soil_from_ngsi(avg_soil)  
    site_provider = WOFOST72SiteDataProvider(WAV=20, SSMAX=1)
    crop_provider = YAMLCropDataProvider(fpath="WOFOST_crop_parameters/")

    yaml_agro = """
    - 2023-08-13:
        CropCalendar:
            crop_name: sorghum
            variety_name: Sorghum_VanHeemst_1988
            crop_start_date: 2023-08-13
            crop_start_type: emergence
            crop_end_date: 2023-11-13
            crop_end_type: harvest
            max_duration: 300
        TimedEvents: null
        StateEvents: null
    """
    agro_provider = yaml.safe_load(yaml_agro)

    weather_provider = NASAPowerWeatherDataProvider(longitude=-45.523917847717236, latitude=-12.170341419421398)

        
    parameter_provider = ParameterProvider(soildata=soil_provider,
                                            cropdata=crop_provider,
                                            sitedata=site_provider)

    print("Sttarting WOFOST")
    wofost = Wofost72_WLP_FD(parameter_provider, weather_provider, agro_provider)
    wofost.run_till_terminate()

    df = pd.DataFrame(wofost.get_output())
    df["day"] = pd.to_datetime(df.day)
    df["unix"] = df["day"].astype(int) / 10**9
    # plt.plot( df.index, df.WWLOW )
    # plt.plot(daily_data.day, daily_data.rainfall/np.max(daily_data.rainfall))
    
    time_start = np.min(df.day)
    time_end   = np.max(df.day)
    time_step  = datetime.timedelta(hours=1)
    time_current = time_start
    func = scipy.interpolate.interp1d(df.unix, df.SM) 

    alpha1 = 0.95
    alpha2 = 0.90
    sm0last = 0.0
    sm1last = 0.0
    sm2last = 0.0

    cosmicswamp.delete_timeseries_for_entity(session, f"SoilProbe:F1-{zoneid}", "SoilDepthProbe")

    while time_current < time_end:
        unix = pd.to_datetime([time_current]).astype(int) / 10**9
        sm0 = func(unix)

        sm1 = ((1 - alpha1) * sm0last + alpha1 * sm0)*1.1
        sm2 = ((1 - alpha2) * sm1last + alpha1 * sm1)*1.1

        information_platform.soildepthprobe.simulate(session, f"SoilProbe:F1-{zoneid}", time_index=time_current.isoformat(), sc0=sm0, sc1=sm1, sc2=sm2, adc_noise=10)
        time_current += time_step
        print(time_current, unix, sm0, f"SoilProbe:F1-{zoneid}")

        sm0last = sm0
        sm1last = sm1
        sm2last = sm2

        print("SM PROP", zoneid, sm0)


import concurrent.futures

zones = information_platform.field.get_associated_zones(session, "Field:1")
# for z in zones:
    # simulate_zone(z)

with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
    executor.map(simulate_zone, zones)

# The ThreadPool will automatically manage the execution of the function in parallel