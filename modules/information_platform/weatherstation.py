
from fastapi import FastAPI, HTTPException
from typing import Union
from fastapi import FastAPI, Request
from fastapi import FastAPI, Header
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from typing import Annotated
from fastapi import FastAPI, Query
import datetime
import time
import math
import statistics

from pcse.db import NASAPowerWeatherDataProvider

import warnings
import itertools
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import matplotlib
import pmdarima as pm

import os
import requests
import json
import logging

import pandas as pd
from typing import List

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson
import dependencies.log_utils as log
import pcse

from .configuration import settings
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.information_platform.managementzone as managementzone

NULL_VALUE = -999
from typing import Any, Dict, AnyStr, List, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

################################################
# MODULE ws_router
################################################
ws_router = APIRouter(
    prefix="/information-platform/weatherstation",
    tags=["information-platform:weatherstation"],
    dependencies=[Depends(settings), Depends(orion.required_headers)]
)
ws_router.verbosity = log.INFO

################################################
# Parameter Helpers
################################################
def MessageIndex(value):                  return orion.Int(value)
def AirPressure(value, unit="Pa"):        return orion.Number(value, unit)
def AirHumidity(value, unit="g/g"):       return orion.Number(value, unit)
def AirTemperature(value, unit="m3/m3"):  return orion.Number(value, unit)
def WindSpeed(value, unit="ms-1"):        return orion.Number(value, unit)
def WindDirection(value, unit="degrees"): return orion.Number(value, unit)
def SolarRadiation(value, unit="W/m3"):   return orion.Number(value, unit)
def RainFall(value, unit="W/m3"):         return orion.Number(value, unit)
def BatteryVoltage(value, unit="V"):      return orion.Number(value, unit)
def StationID(value):                     return orion.String(value)
def StationSource(value):                 return orion.String(value)
def StationType(value):                   return orion.String(value)


################################################
# Device Mappings
################################################
mqtt_mapping = {
    "Dm":  ["winddirection", WindDirection, "D"],
    "Sm":  ["windspeed", WindSpeed, "M"],
    "Ta":  ["airtemperature", AirTemperature, "C"],
    "Ua":  ["airhumidity", AirHumidity, "P"],
    "Pa":  ["airpressure", AirPressure, "H"],
    "Rc":  ["rainfall", RainFall, "M"],
    "Vs":  ["batteryvoltage", BatteryVoltage, "V"],
    "Id":  ["stationid", StationID, ""]
}

################################################
# ROUTES
################################################

# -----------------------------------
# Device creation routine.
#
@ws_router.get("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    attrs: List[str] = None,
                    time_index: str = None,
                    location: List[float] = geojson.point(),
                    i0: int = 0,
                    at: float = 0.0,
                    ap: float = 0.0,
                    ah: float = 0.0,
                    ws: float = 0,
                    wd: float = 0,
                    rf: float = 0,
                    sr: float = 0,
                    bv: float = 0,
                    station_id: str = "",
                    station_source: str = "",
                    station_type: str = "",
                    jsondata: JSONStructure = None
    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    entity_type = "WeatherStation"
    body = ngsi.compile_entity(jsondata, entity_id, entity_type, time_index, attrs)

    # Entity header variables
    orion.set_state_source(body, "CREATION", "API")
    ngsi.set_default(body, "location",      location)
    ngsi.set_default(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_default(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_default(body, "messageindex",     MessageIndex(i0))
    ngsi.set_default(body, "airtemperature",  AirTemperature(at)) 
    ngsi.set_default(body, "airpressure",     AirPressure(ap)) 
    ngsi.set_default(body, "airhumidity",     AirHumidity(ah)) 
    ngsi.set_default(body, "windspeed",      WindSpeed(ws)) 
    ngsi.set_default(body, "winddirection",  WindDirection(wd)) 
    ngsi.set_default(body, "solarradiation", SolarRadiation(sr)) 
    ngsi.set_default(body, "batteryvoltage", BatteryVoltage(bv)) 
    ngsi.set_default(body, "rainfall", RainFall(rf)) 

    ngsi.set_default(body, "stationid",      StationID(station_id)) 
    ngsi.set_default(body, "stationsource",  StationSource(station_source)) 
    ngsi.set_default(body, "stationtype",    StationType(station_type)) 

    cosmicswamp.create_entity(request, entity_id, entity_type, jsondata=body)
    cosmicswamp.update_entity(request, entity_id, entity_type, jsondata=body)

    return body


# -----------------------------------
# Device update routine.
# 
# Allows simulated or real data uploads
@ws_router.post("/up/{entity_id}")
def update(request: Request,
                    entity_id,                      # Device Entity in Orion
                    attrs: List[str] = None,        # Additional custom attributes
                    time_index: str = None,
                    location: List[float] = None,
                    i0: int = None,
                    at: float = None,
                    ap: float = None,
                    ah: float = None,
                    ws: float = None,
                    wd: float = None,
                    sr: float = None,
                    bv: float = None,
                    rf: float = None,
                    station_id: str = None,
                    station_source: str = None,
                    station_type: str = None,
                    payload_type: str = None,
                    jsondata: JSONStructure = None,
                    payload_data: JSONStructure = None,
                    inference: bool = False

    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    entity_type = "WeatherStation"
    # body = cosmicswamp.compile_entity_state_at_time(request, entity_id, entity_type, time_index, attrs, jsondata, inference=inference)
    body = ngsi.compile_entity(jsondata, entity_id, entity_type, time_index, attrs)

    # Entity header variables
    ngsi.set_override(body, "location",      location)
    ngsi.set_override(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_override(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_override(body, "messageindex",    MessageIndex(i0))
    ngsi.set_override(body, "messageindex",    MessageIndex(i0))
    ngsi.set_override(body, "airtemperature",  AirTemperature(at)) 
    ngsi.set_override(body, "airpressure",     AirPressure(ap)) 
    ngsi.set_override(body, "airhumidity",     AirHumidity(ah)) 
    ngsi.set_override(body, "windspeed",      WindSpeed(ws)) 
    ngsi.set_override(body, "winddirection",  WindDirection(wd)) 
    ngsi.set_override(body, "solarradiation", SolarRadiation(sr)) 
    ngsi.set_override(body, "batteryvoltage", BatteryVoltage(bv))
    ngsi.set_override(body, "rainfall",       RainFall(rf)) 

    ngsi.set_override(body, "stationid",      StationID(station_id)) 
    ngsi.set_override(body, "stationsource",  StationSource(station_source)) 
    ngsi.set_override(body, "stationtype",    StationType(station_type)) 

    log.debug(ws_router,"WEATHER UPLOAD : ")

    log.debug(ws_router,body, at, ap, ah)

    if not cosmicswamp.has_current_entity_from_id(request, entity_id):
        cosmicswamp.create_entity(request, entity_id, entity_type, jsondata=body)
    else:
        cosmicswamp.update_entity(request, entity_id, entity_type, jsondata=body)
        

@ws_router.post("/iotagent/{entity_id}")
def iotagent(request: Request,
            entity_id,
            time_index: str = None,
            test_addition: str = None,
            payload_type: str = None,
            payload_data: JSONStructure = None):
    
    # Parsing routines
    # - Thingsboard MQTT TTN Parser based on decoded_payload
    headers = orion.get_fiware_headers(request)
    body = cosmicswamp.build_entity_table(entity_id, "WeatherStation", time_index, None, None)

    # Parsing routines
    # - Thingsboard MQTT TTN Parser based on decoded_payload
    if payload_type == "mqtt_ttn":
        orion.set_state_source(body, "RAW", "TTN_MQTT")

        payload_data = payload_data["payload_data"]
        print("PAYLOAD DATA", payload_data)
        data = payload_data.strip().split(",")
        # 0R0,Dm=219D,Sm=1.3M,Ta=24.5C,Ua=68.7P,Pa=913.0H,Rc=0.00M,Vs=12.6V,Id=Cidade1\r\n
        dataset = {}
        if data[0] == "0R0":
            for attr in data:
                if attr == "0R0":
                    continue
                key, val = attr.split("=")
                dataset[key] = val

        print("MOD DATA", dataset)
        # Build NGSI data from strip list hardcoded format.
        for key in dataset:
            if key in mqtt_mapping:
                name, unit, parse = mqtt_mapping[key]
                
                val = dataset[key].strip(parse)
                ngsi.set_value(body, name, unit(val))
                
        ngsi.set_override(body, "stationid",      StationID(entity_id)) 
        ngsi.set_override(body, "stationsource",  StationSource("MQTT")) 
        ngsi.set_override(body, "stationtype",    StationType("MQTT")) 

        # -- Raw data needs to be calibrated
        orion.set_state_source(body, "CALIBRATED", "TTN_MQTT")


    print("IoT Message Data", headers, body)
    update(request, entity_id, time_index=time_index, jsondata=body)

    return body



def update_from_pcse_wdp(request : Request, entity_id : str, weatherdata, time_start):

    update(request, 
        entity_id, 
        time_index=time_start.isoformat(),
        at=weatherdata["TEMP"],
        ap=calculate_atmo_pressure_from_temp(weatherdata["ELEV"], weatherdata["TEMP"]),
        ah=relhum_from_vap(weatherdata["VAP"], weatherdata["TEMP"]),
        ws=weatherdata["WIND"],
        rf=weatherdata["RAIN"],
        wd=0,
        sr=weatherdata["IRRAD"],
        bv=1.0, 
        inference=False
    )




def calculate_vapor_pressure(temperature_Celsius, relative_humidity_percent):
    # Convert temperature to Kelvin
    temperature_kelvin = temperature_Celsius + 273.15

    # Calculate Saturation Vapor Pressure (e_s) using Magnus-Tetens formula
    e_s = 6.1078 * 10**((7.5 * temperature_Celsius) / (temperature_Celsius + 237.3))

    # Convert relative humidity to a decimal
    relative_humidity_decimal = relative_humidity_percent / 100.0

    # Calculate Vapor Pressure (e)
    e = relative_humidity_decimal * e_s

    return e

def calculate_absolute_pressure(vapor_pressure, atmospheric_pressure):
    return vapor_pressure + atmospheric_pressure

import numpy as np
def atmo_pressure_from_temp(ELEV, TMPA):
    PBAR = 1013.*np.exp(-0.034*ELEV/(TMPA+273.))
    return PBAR

SatVapourPressure = lambda temp: 0.6108 * np.exp((17.27 * temp) / (237.3 + temp))

def relhum_from_vap(vap, temp):
    return (vap/(SatVapourPressure(temp)*0.1))/100.0


from pcse.base.weather import WeatherDataProvider, WeatherDataContainer
from pcse.fileinput import CABOFileReader

def calculate_angstrom(lat):
    # Constants
    earth_radius_km = 6371.0  # Radius of the Earth in kilometers

    # Convert latitude from degrees to radians
    lat_rad = math.radians(lat)

    # Calculate angstromA (length of 1 degree of latitude)
    angstromA = (2 * math.pi * earth_radius_km) / 360.0

    # Calculate angstromB (length of 1 degree of longitude)
    angstromB = angstromA * math.cos(lat_rad)

    return angstromA, angstromB

angstDict = {}

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
        self._last_date  = pd.to_datetime(np.max(df["day"])).date()
        self._first_date = pd.to_datetime(np.min(df["day"])).date()

        self.df = df
        self.df["day"] = pd.to_datetime(self.df.day)

        self.ANGSTA = 0.0
        self.ANGSTB = 0.0
        self.elevation = 0.0

        # if (f"{latitude}-{longitude}" in angstDict):
            # self.ANGSTA, self.ANGSTB, self.elevation = angstDict[f"{latitude}-{longitude}"]
            # self.future_df = self.build_future_predictor()
        # else:
        print("MAKING WDP", latitude, longitude)
        self.local_nasa_wdp = NASAPowerWeatherDataProvider(longitude=self.longitude, latitude=self.latitude)
        angstDict[f"{latitude}-{longitude}"] = (self.local_nasa_wdp.angstA, self.local_nasa_wdp.angstB, self.local_nasa_wdp.elevation)
        self.ANGSTA, self.ANGSTB, self.elevation = angstDict[f"{latitude}-{longitude}"]


        # Make a future predictor for this site.

        #self.future_df = self.build_future_predictor()

        print("ANGSTA", self.ANGSTA, self.ANGSTB)


    def build_future_predictor(self):

        start_date=self._last_date
        print("START_DATE", start_date)
        pre_date = (pd.to_datetime(self._last_date) - datetime.timedelta(days=365*10)).date()

        dataset = {
            "Date":   [],
            "IRRAD": [],
            "TMIN":  [],
            "TMAX":  [],
            "VAP":   [],
            "RAIN":  [],
            "E0":    [],
            "ES0":   [],
            "ET0":   [],
            "WIND":  [],
            "TEMP":  []
        }

        while pre_date < start_date:
            pre_date += datetime.timedelta(days=1)

            try:
                vals = self.local_nasa_wdp(pre_date)
            except:
                continue

            dataset["Date"].append(pre_date)
            dataset["IRRAD"].append( vals.IRRAD )
            dataset["TMIN"].append( vals.TMIN )
            dataset["TMAX"].append( vals.TMAX )
            dataset["VAP"].append( vals.VAP )
            dataset["RAIN"].append( vals.RAIN )
            dataset["E0"].append( vals.E0 )
            dataset["ES0"].append( vals.ES0 )
            dataset["ET0"].append( vals.ET0 )
            dataset["WIND"].append( vals.WIND )
            dataset["TEMP"].append( vals.TEMP )

        nasadf = pd.DataFrame(data=dataset)

        for key in nasadf:
            if "Date" in key: continue
            nasadf[key+"_mean"] = nasadf[key].mean()
            nasadf[key] /= nasadf[key+"_mean"]

        nasadf.isnull().sum()
        nasadf = nasadf.dropna()
        nasadf.isnull().sum()

        nasadf['Date'] = pd.to_datetime(nasadf['Date'])
        nasadf["Month"] = pd.PeriodIndex(nasadf['Date'], freq="W")


        nasadf = nasadf.groupby("Date", "Month").mean().reset_index()
        print(nasadf)

        # nasadf = nasadf.set_index("Day")
        # nasadf = nasadf.drop("Month", axis=1)

        for key in nasadf:
            if key == "Month": continue
            if "mean" in key: continue
            decomposition = sm.tsa.seasonal_decompose(nasadf[key], period=52, model="additive")
            
            # fig = decomposition.plot()
            # plt.show()

            nasadf[key+"_trend"] = decomposition.trend
            nasadf[key+"_seasonal"] = decomposition.seasonal
            nasadf[key+"_residual"] = decomposition.resid


        nasadf = nasadf.resample('D')
        nasadf = nasadf.interpolate(method='linear', fill_value=0.0)
        nasadf["day_of_year"] = pd.to_datetime(nasadf.index).day_of_year
        sdf = nasadf.groupby(["day_of_year"]).mean()
        print(sdf)

        # self._last_date = self._last_date + datetime.timedelta(days=2*365)

        return sdf

    def seasonal_forecast(self, day):

            current_day_of_year = pd.to_datetime(day).day_of_year

            row = self.future_df.loc[current_day_of_year]
            wdc = {}
            
            sitevar = ["LAT", "LON", "ELEV"]
            required = ["IRRAD", "TMIN", "TMAX", "VAP", "RAIN", "E0", "ES0", "ET0", "WIND"]
            optional = ["SNOWDEPTH", "TEMP", "TMINRA"]

            for key in sitevar + required + optional:
                wdc[key] = 0.0
            
            for key in ["IRRAD","TMIN","TMAX","VAP","RAIN","WIND","TEMP"]:
                value = (row[f"{key}_seasonal"]+row[f"{key}_trend"])*row[f"{key}_mean"]
                wdc[key] = value

            wdc["LAT"] = self.latitude
            wdc["LON"] = self.longitude
            wdc["ELEV"] = self.elevation
            wdc["DAY"] = day

            e0, es0, et0 = pcse.util.reference_ET(day, self.latitude, self.elevation, 
                    wdc["TMIN"], wdc["TMAX"], wdc["IRRAD"], wdc["VAP"], wdc["WIND"],
                    self.ANGSTA, self.ANGSTB )

            wdc["E0"] = e0/10.
            wdc["ES0"] = es0/10.
            wdc["ET0"] = et0/10.
            wdc["SNOWDEPTH"] = 0.0

            if wdc["RAIN"] < 0: wdc["RAIN"] = 0

            wdc_date = WeatherDataContainer(**wdc)
            return wdc_date

    def __call__(self, day, member_id=0):      
        day =  pd.to_datetime(day)

        if day < pd.to_datetime(pd.to_datetime(np.max(self.df["day"])).date()):
            
            entry = self.df[self.df.day == pd.to_datetime(day)]

            if len(entry) == 0: 
                return self.seasonal_forecast(day)

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
            wdc["VAP"] = float(pcse.util.vap_from_relhum(entry["airhumidity"]*100.0,entry["airtemperature"]))
            wdc["RAIN"] = float(entry["rainfall"])
            wdc["WIND"] = float(entry["windspeed"])
            wdc["TEMP"] = float(entry["airtemperature"])

            e0, es0, et0 = pcse.util.reference_ET(day, self.latitude, self.elevation, 
                    wdc["TMIN"], wdc["TMAX"], wdc["IRRAD"], wdc["VAP"], wdc["WIND"],
                    self.ANGSTA, self.ANGSTB )

            wdc["E0"] = e0/10.
            wdc["ES0"] = es0/10.
            wdc["ET0"] = et0/10.
            wdc["SNOWDEPTH"] = 0.0


        # body = {
        #     "airtemperature": AirTemperature(wdp_row["TEMP"]),
        #     "airpressure": AirPressure(atmo_pressure_from_temp(wdp_row["ELEV"], wdp_row["TEMP"])),
        #     "airhumidity": AirHumidity(relhum_from_vap(wdp_row["VAP"], wdp_row["TEMP"])),
        #     "windspeed": WindSpeed(wdp_row["WIND"]),
        #     "rainfall": RainFall(wdp_row["RAIN"]),
        #     "winddirection": WindDirection(0),
        #     "solarradiation": SolarRadiation(wdp_row["IRRAD"]),
        #     "batteryvoltage": BatteryVoltage(1.0),
        #     "TimeInstant": orion.TimeInstant(time_index.isoformat())
        # }

            wdc_date = WeatherDataContainer(**wdc)

        else:
            return self.seasonal_forecast(day)
        

        return wdc_date


def build_wdp_from_weatherstation(session, station_name):

    # Get Time Series Weather Data
    weather_data = cosmicswamp.get_series_data_for_entity(session, station_name, attrs=["*"], limit=1000000)
    data = pd.DataFrame(data=(weather_data))

    # Merge data to get average per day
    data["date"] = pd.to_datetime(data["time_index"], unit="ms")
    data["day"]  = data["date"].dt.date
    time_data = data[["day","airtemperature","airpressure","airhumidity","windspeed","winddirection","solarradiation","batteryvoltage","rainfall"]]
    daily_data = time_data.groupby("day").mean().reset_index()
    daily_data["date"] = pd.to_datetime(daily_data["day"])

    daily_data["airtemperature_min"] = time_data.groupby("day").min().reset_index()["airtemperature"]
    daily_data["airtemperature_max"] = time_data.groupby("day").max().reset_index()["airtemperature"]

    # Setup PCSE crpo information
    weather_provider = PandasWeatherDataProvider(daily_data)
    return weather_provider

def to_unix(dt):
    return float(time.mktime(dt.timetuple()))


def interpolate_values_from_datetime(t0, v0, t1, v1, ti):
    tw = (to_unix(t1)-to_unix(t0))
    vw = (v1-v0)
    td = (to_unix(ti)-to_unix(t0))/tw
    return v0 + vw*td


def interpolate_pcse_wdp_to_ngsi(wdp, time_index):

    d0 = time_index.date()
    d1 = (time_index + datetime.timedelta(hours=24)).date()

    w0 = wdp(d0)
    w1 = wdp(d1)
    wc = wdp(d1)

    # Assume readings are at noon
    t0 = d0 + datetime.timedelta(hours=12)
    t1 = d1 + datetime.timedelta(hours=12)

    wdp_row = {}
    wdp_row["ELEV"] = w0.ELEV
    wdp_row["TMIN"]  = interpolate_values_from_datetime(t0, w0.TMIN, t1, w1.TMIN, time_index)
    wdp_row["TMAX"]  = interpolate_values_from_datetime(t0, w0.TMAX, t1, w1.TMAX, time_index)
    wdp_row["IRRAD"] = interpolate_values_from_datetime(t0, w0.IRRAD, t1, w1.IRRAD, time_index)
    wdp_row["VAP"]   = interpolate_values_from_datetime(t0, w0.VAP, t1, w1.VAP, time_index)
    wdp_row["RAIN"]  = interpolate_values_from_datetime(t0, w0.RAIN, t1, w1.RAIN, time_index)
    wdp_row["WIND"]  = interpolate_values_from_datetime(t0, w0.WIND, t1, w1.WIND, time_index)
    wdp_row["E0"]    = interpolate_values_from_datetime(t0, w0.E0, t1, w1.E0, time_index)
    wdp_row["ES0"]   = interpolate_values_from_datetime(t0, w0.ES0, t1, w1.ES0, time_index)
    wdp_row["ET0"]   = interpolate_values_from_datetime(t0, w0.ET0, t1, w1.ET0, time_index)
    wdp_row["TEMP"]  = interpolate_values_from_datetime(t0, w0.TEMP, t1, w1.TEMP, time_index)

    body = {
        "airtemperature": AirTemperature(wdp_row["TEMP"]),
        "airpressure": AirPressure(atmo_pressure_from_temp(wdp_row["ELEV"], wdp_row["TEMP"])),
        "airhumidity": AirHumidity(relhum_from_vap(wdp_row["VAP"], wdp_row["TEMP"])),
        "windspeed": WindSpeed(wdp_row["WIND"]),
        "rainfall": RainFall(wdp_row["RAIN"]),
        "winddirection": WindDirection(0),
        "solarradiation": SolarRadiation(wdp_row["IRRAD"]),
        "batteryvoltage": BatteryVoltage(1.0),
        "TimeInstant": orion.TimeInstant(time_index.isoformat())
    }

    return body



def solarradiation_from_cloud_cover(cloud_cover_percentage):
    """
    Estimate solar radiation based on cloud cover percentage.

    Parameters:
    - cloud_cover_percentage: Cloud cover percentage (0 to 100).

    Returns:
    - Estimated solar radiation in watts per square meter (W/m^2).
    """
    # Assuming clear-sky radiation for reference (in W/m^2)
    clear_sky_radiation = 1000  

    # Calculate the reduction factor based on cloud cover percentage
    reduction_factor = 1 - (cloud_cover_percentage / 100)

    # Estimate solar radiation by applying the reduction factor
    estimated_radiation = clear_sky_radiation * reduction_factor

    return estimated_radiation



def pcse_wdp_to_ngsi(wdp_row):

    body = {
        "airtemperature": AirTemperature(wdp_row.TEMP),
        "airpressure": AirPressure(atmo_pressure_from_temp(wdp_row.ELEV, wdp_row.TEMP)),
        "airhumidity": AirHumidity(relhum_from_vap(wdp_row.VAP, wdp_row.TEMP)),
        "windspeed": WindSpeed(wdp_row.WIND),
        "rainfall": RainFall(wdp_row.RAIN),
        "winddirection": WindDirection(0),
        "solarradiation": SolarRadiation(wdp_row.IRRAD),
        "batteryvoltage": BatteryVoltage(1.0)
    }

    return body