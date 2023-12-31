from fastapi import FastAPI, Header, Request, APIRouter, Depends, HTTPException, Query
from fastapi_utils.tasks import repeat_every

from typing import Union, Annotated, List, Any, Dict, AnyStr, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

import datetime
import time
import math
import statistics
import os
import requests
import json
import logging
import pandas as pd
import scipy
import numpy as np
import pvlib


import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson

import modules.iot_platform.cosmicswamp as cosmicswamp

import modules.information_platform.configuration as configuration
import modules.information_platform.managementzone as managementzone


###################################################
# ENTITY MODEL : WeatherForecast
###################################################
ENTITY_TYPE = "WeatherForecast"
ENTITY_TYPE_lower = ENTITY_TYPE.lower()


################################################
# MODULE ROUTER
################################################
router = APIRouter(
    prefix="/information-platform/weatherforecast",
    tags=["information-platform","weatherforecast"],
    dependencies=[Depends(configuration.settings), Depends(orion.required_headers)]
)


################################################
# PARAMETER DEFINITIONS
################################################
def MessageIndex(value):                         return orion.Int(value)
def CloudProbability(value): return orion.Number(value)
def Temperature(value): return orion.Number(value)
def RainProbability(value): return orion.Number(value)
def RainIntensity(value): return orion.Number(value)
def AirHumidity(value): return orion.Number(value)
def CloudCover(value): return orion.Number(value)
def WindSpeed(value): return orion.Number(value)
def WindDirection(value): return orion.Number(value)
def Daylight(value): return orion.Number(value)
def RequestStatus(value): return orion.String(value)
def SolarRadiation(value): return orion.Number(value)



import pandas as pd
import pvlib
import datetime

def estimate_daylight_intensity(latitude, longitude,datetime_obj):
    """
    Estimate daylight intensity based on latitude, longitude, date, and time.

    Parameters:
    - latitude: Latitude of the location.
    - longitude: Longitude of the location.
    - date: Date in the format 'YYYY-MM-DD'.
    - time: Time in the format 'HH:mm:ss'.

    Returns:
    - Estimated daylight intensity in W/m^2.
    """

    # Create a pandas DataFrame with the datetime
    times = pd.date_range(datetime_obj, periods=1, freq='H', tz='UTC')
    df = pd.DataFrame({'times': times})

    # Set location coordinates
    location = pvlib.location.Location(latitude, longitude)

    # Calculate solar position
    solar_position = pvlib.solarposition.get_solarposition(df.index, latitude, longitude)

    # Calculate extraterrestrial radiation
    dni_extra = pvlib.irradiance.get_extra_radiation(df.index)

    # Calculate air mass
    airmass = pvlib.atmosphere.get_relative_airmass(solar_position['apparent_zenith'])

    # Calculate Global Horizontal Irradiance (GHI)
    ghi = pvlib.irradiance.get_total_irradiance(df.index, latitude, longitude,
                                             dni_extra=dni_extra,
                                             solar_position=solar_position,
                                             airmass=airmass)

    return ghi.iloc[0]



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



################################################
# Device Mappings
################################################
mqtt_mapping = {
    "I":   ["messageIndex", MessageIndex],
}

# Helpere Functions

def CheckAccuWeather(citykey):
    if ("Message" in citykey and "exceeded" in citykey["Message"]):
        return False
    return True

def GetAccuWeatherData(apikey, lat, lon):
    print("Getting AccuWeather")

    url = f"http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey={apikey}&q={lat},{lon}&language=en-us"
    r = requests.get(url)
    if not CheckAccuWeather(r.json()): return []
    citykey = r.json()["Key"]

    url = f"http://dataservice.accuweather.com//forecasts/v1/hourly/12hour/{citykey}?apikey={apikey}&metric=true"
    r = requests.get(url)
    hourly_forecast = r.json()
    if not CheckAccuWeather(hourly_forecast): return []

    url = f"http://dataservice.accuweather.com//forecasts/v1/daily/5day/{citykey}?apikey={apikey}&metric=true"
    r = requests.get(url)
    daily_forecast = r.json()
    if not CheckAccuWeather(daily_forecast): return []

    print(daily_forecast)
            
    data = {
        "date": [],
        "cloud_probability": [],
        "airpressure": [],
        "airtemperature_min": [],
        "airtemperature": [],
        "airtemperature_max": [],
        "rain_probability": [],
        "rain_intensity": [],
        "airhumidity": [],
        "cloud_cover": [],
        "wind_speed": [],
        "wind_direction": [],
        "source": [],
        "daylight": [],
        "solarradiation": []
    }


    for fc in (hourly_forecast):
        print(fc, data)
        data["date"].append( pd.to_datetime(fc["DateTime"]) )
        data["airtemperature"].append( fc["Temperature"]["Value"] )
        data["airtemperature_min"].append( fc["Temperature"]["Value"] )
        data["airtemperature_max"].append( fc["Temperature"]["Value"] )
        data["airhumidity"].append( None )
        data["airpressure"].append( None )
        data["wind_speed"].append( None )
        data["wind_direction"].append( None )
        data["daylight"].append( fc["IsDaylight"] )
        data["source"].append("AccuWeather")

        if fc["HasPrecipitation"]:
            data["rain_probability"].append( fc["PrecipitationProbability"] )
            intensity = fc["PrecipitationIntensity"]
            if intensity == "Light": data["rain_intensity"].append( 0.33 )
            if intensity == "Moderate": data["rain_intensity"].append( 0.66 )
            if intensity == "Heavy": data["rain_intensity"].append( 1.00 )
        else:
            data["rain_intensity"].append( 0.0 )
            data["rain_probability"].append( fc["PrecipitationProbability"] )

        data["cloud_cover"].append(None)
        data["cloud_probability"].append(None)
        data["solarradiation"].append( None )



    for fc in (daily_forecast["DailyForecasts"]):

        print(fc)
        data["date"].append(pd.to_datetime(fc["Date"]))
        data["airtemperature"].append( (fc["Temperature"]["Minimum"]["Value"]+fc["Temperature"]["Maximum"]["Value"])/2 )
        data["airtemperature_min"].append( fc["Temperature"]["Minimum"]["Value"] )
        data["airtemperature_max"].append(  fc["Temperature"]["Maximum"]["Value"] ) 
        data["airhumidity"].append( None )
        data["airpressure"].append( None )
        data["wind_speed"].append( None )
        data["wind_direction"].append( None )
        data["daylight"].append( 1.0 )
        data["source"].append("AccuWeather")
        
        if fc["Day"]["HasPrecipitation"]:
            data["rain_probability"].append( 1.0 )
            intensity = fc["Day"]["PrecipitationIntensity"]
            if intensity == "Light": data["rain_intensity"].append( 0.33 )
            if intensity == "Moderate": data["rain_intensity"].append( 0.66 )
            if intensity == "Heavy": data["rain_intensity"].append( 1.00 )
        else:
            data["rain_intensity"].append( 0.0 )
            data["rain_probability"].append( 0.0 )

        data["cloud_cover"].append(None)
        data["cloud_probability"].append(None)
        data["solarradiation"].append( None )

        data["date"].append(pd.to_datetime(fc["Date"]) + datetime.timedelta(seconds=86400/2))
        data["airtemperature"].append( (fc["Temperature"]["Minimum"]["Value"]+fc["Temperature"]["Maximum"]["Value"])/2 )
        data["airtemperature_min"].append( fc["Temperature"]["Minimum"]["Value"] )
        data["airtemperature_max"].append(  fc["Temperature"]["Maximum"]["Value"] ) 
        data["airhumidity"].append( None )
        data["airpressure"].append( None )
        data["wind_speed"].append( None )
        data["wind_direction"].append( None )
        data["daylight"].append( 0.0 )
        data["source"].append("AccuWeather")
        
        if fc["Night"]["HasPrecipitation"]:
            data["rain_probability"].append( 1.0 )
            print(fc)
            intensity = fc["Night"]["PrecipitationIntensity"]
            if intensity == "Light": data["rain_intensity"].append( 0.33 )
            if intensity == "Moderate": data["rain_intensity"].append( 0.66 )
            if intensity == "Heavy": data["rain_intensity"].append( 1.00 )
        else:
            data["rain_intensity"].append( 0.0 )
            data["rain_probability"].append( 0.0 )

        data["cloud_cover"].append(None)
        data["cloud_probability"].append(None)
        data["solarradiation"].append( None )


    for key in data:
        print(key,len(data[key]))
    df = pd.DataFrame(data=data)

    return df

def GetOpenWeatherData(apikey, lat, lon):

    print("Getting OpenWeather")
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={apikey}"
    r = requests.get(url)
    current_data = r.json()

    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={apikey}"
    r = requests.get(url)
    hourly_forecast = r.json()
            
    data = {
        "date": [],
        "cloud_probability": [],
        "airpressure": [],
        "airtemperature_min": [],
        "airtemperature": [],
        "airtemperature_max": [],
        "rain_probability": [],
        "rain_intensity": [],
        "airhumidity": [],
        "cloud_cover": [],
        "wind_speed": [],
        "wind_direction": [],
        "source": [],
        "daylight": [],
        "solarradiation": []
    }

    weatherlist = [current_data]
    for key in hourly_forecast["list"]:
        weatherlist.append(key)

    for key in weatherlist:
        data["source"].append("OpenWeather")
        data["daylight"].append(None)
        data["date"].append(pd.to_datetime(key["dt"], unit="s"))
        data["airtemperature"].append(key["main"]["temp"] - 273.3)
        data["airtemperature_min"].append(key["main"]["temp_min"] - 273.3)
        data["airtemperature_max"].append(key["main"]["temp_max"] - 273.3)
        data["airpressure"].append(key["main"]["pressure"] )
        data["airhumidity"].append(key["main"]["humidity"] )
        data["cloud_probability"].append( key["clouds"]["all"] )
        data["cloud_cover"].append( key["clouds"]["all"] )
        data["wind_speed"].append( key["wind"]["speed"] )
        data["wind_direction"].append( key["wind"]["deg"] )
        data["solarradiation"].append( (100.0-(key["clouds"]["all"]))/100.0 )
        
        rainkey = key["weather"][0]
        if rainkey["description"] == "light rain": 
            data["rain_probability"].append(1.0)
            data["rain_intensity"].append(0.33)
        elif rainkey["description"] == "moderate rain": 
            data["rain_probability"].append(1.0)
            data["rain_intensity"].append(0.66)
        elif rainkey["description"] == "heavy rain": 
            data["rain_probability"].append(1.0)
            data["rain_intensity"].append(1.00)
        else:
            data["rain_probability"].append(0.0)
            data["rain_intensity"].append(0.0)

        
    for key in data:
        print(key, len(data[key]))
    df = pd.DataFrame(data=data)

    return df


################################################
# ROUTES CREATE/UP/DELETE
################################################
@router.get("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    time_index: str = None,
                    location: JSONStructure = None,
                    jsondata: JSONStructure = None,
                    apitype: str = None,
                    apikey: str = None,
                    cloud_probability: float = None,
                    airtemperature_min: float = None,
                    airtemperature_max: float = None,
                    airtemperature: float = None,
                    rain_probability: float = None,
                    rain_intensity: float = None,
                    airhumidity: float = None,
                    cloud_cover: float = None,
                    solarradiation: float = None,
                    wind_speed: float = None,
                    wind_direction: float = None,
                    daylight: float = None,
                    status: str = "CREATE"
    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    body = ngsi.compile_entity(jsondata, entity_id, ENTITY_TYPE, time_index, [])

    # Entity header variables
    orion.set_state_source(body, "CREATION", "API")
    ngsi.set_default(body, "location",      location)
    ngsi.set_default(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_default(body, "ForecastInstant",   orion.TimeInstant(time_index))
    ngsi.set_default(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_default(body, "apitype", orion.String(apitype))
    ngsi.set_default(body, "apikey", orion.String(apikey))

    ngsi.set_default(body, "cloud_probability", CloudProbability(cloud_probability))
    ngsi.set_default(body, "airtemperature_min", Temperature(airtemperature_min))
    ngsi.set_default(body, "airtemperature_max", Temperature(airtemperature_max))
    ngsi.set_default(body, "airtemperature", Temperature(airtemperature))
    ngsi.set_default(body, "rain_probability", RainProbability(rain_probability))
    ngsi.set_default(body, "rain_intensity", RainIntensity(rain_intensity))
    ngsi.set_default(body, "airhumidity", AirHumidity(airhumidity))
    ngsi.set_default(body, "cloud_cover", CloudCover(cloud_cover))
    ngsi.set_default(body, "wind_speed", WindSpeed(wind_speed))
    ngsi.set_default(body, "wind_direction", WindDirection(wind_direction))
    ngsi.set_default(body, "daylight", Daylight(daylight))
    ngsi.set_default(body, "solarradiation", SolarRadiation(solarradiation))

    ngsi.set_default(body, "status", RequestStatus(status))

    cosmicswamp.create_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)

    return body

@router.get("/update/{entity_id}")
def update(request: Request,
                    entity_id,
                    time_index: str = None,
                    forecast_time_index: str = None,
                    location: JSONStructure = None,
                    jsondata: JSONStructure = None,
                    apitype: str = None,
                    apikey: str = None,
                    cloud_probability: float = None,
                    temperature_min: float = None,
                    temperature_max: float = None,
                    temperature: float = None,
                    rain_probability: float = None,
                    rain_intensity: float = None,
                    airhumidity: float = None,
                    cloud_cover: float = None,
                    wind_speed: float = None,
                    wind_direction: float = None,
                    daylight: float = None,
                    status: str = None,
                    solarradiation: float = None
    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    body = ngsi.compile_entity(jsondata, entity_id, ENTITY_TYPE, time_index, [])

    # Entity header variables
    orion.set_state_source(body, "CREATION", "API")
    ngsi.set_override(body, "location",      location)
    ngsi.set_override(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_override(body, "ForecastInstant",   orion.TimeInstant(forecast_time_index))
    ngsi.set_override(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_override(body, "apitype", orion.String(apitype))
    ngsi.set_override(body, "apikey", orion.String(apikey))

    ngsi.set_override(body, "cloud_probability", CloudProbability(cloud_probability))
    ngsi.set_override(body, "temperature_min", Temperature(temperature_min))
    ngsi.set_override(body, "temperature_max", Temperature(temperature_max))
    ngsi.set_override(body, "temperature", Temperature(temperature))
    ngsi.set_override(body, "rain_probability", RainProbability(rain_probability))
    ngsi.set_override(body, "rain_intensity", RainIntensity(rain_intensity))
    ngsi.set_override(body, "airhumidity", AirHumidity(airhumidity))
    ngsi.set_override(body, "cloud_cover", CloudCover(cloud_cover))
    ngsi.set_override(body, "wind_speed", WindSpeed(wind_speed))
    ngsi.set_override(body, "wind_direction", WindDirection(wind_direction))
    ngsi.set_override(body, "daylight", Daylight(daylight))
    ngsi.set_override(body, "status", RequestStatus(status))
    ngsi.set_override(body, "solarradiation", SolarRadiation(solarradiation))

    cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    print(body)
    return body


@router.get("/refresh")
def refresh_event():
    """
    Loops over available Weather Forecast instances in the current sesssion.
    """    

    # Sessions need to be run for all possible maps.
    session_list = cosmicswamp.get_session()
    for pathcombo in session_list["sessions"]["value"]:
        service, servicepath = pathcombo.split("/")
        session = orion.session(service,"/" + servicepath)

        # Get Weather Forecasts
        weather_forecasters = cosmicswamp.get_all_current_entities_of_type(session, "WeatherForecast")
        for wf in weather_forecasters:

            lon = wf["location"]["value"]["coordinates"][0]
            lat = wf["location"]["value"]["coordinates"][1]
            apikey = wf["apikey"]["value"]
            apitype = wf["apitype"]["value"]

            df = []
            if apitype == "AccuWeather": df = GetAccuWeatherData(apikey, lat, lon)
            if apitype == "OpenWeather": df = GetOpenWeatherData(apikey, lat, lon)

            if len(df) == 0: 
                update(session, wf["id"], status="FAILED" )
                continue

            ForecastInstant = df.iloc[0]["date"]

            body = wf
            for i in range(len(df)):
                row = df.iloc[i]

                print("ROW",row["date"])
                wf["TimeInstant"] = orion.TimeInstant(row["date"])
                wf["ForecastInstant"] = orion.TimeInstant(ForecastInstant)

                wf["cloud_probability"] = CloudProbability(row["cloud_probability"])
                wf["airtemperature_min"] = Temperature(row["airtemperature_min"])
                wf["airtemperature_max"] = Temperature(row["airtemperature_max"])
                wf["airtemperature"] = Temperature(row["airtemperature"])
                wf["rain_probability"] = RainProbability(row["rain_probability"])
                wf["rain_intensity"] = RainIntensity(row["rain_intensity"])
                wf["airhumidity"] = AirHumidity(row["airhumidity"])
                wf["cloud_cover"] = CloudCover(row["cloud_cover"])
                wf["wind_speed"] = WindSpeed(row["wind_speed"])
                wf["wind_direction"] = WindDirection(row["wind_direction"])
                wf["daylight"] = Daylight(row["daylight"])
                wf["solarradiation"] = SolarRadiation(row["solarradiation"])
        
                update(session, wf["id"], jsondata=body, time_index=wf["TimeInstant"]["value"], status="REQUESTED" )

###################################################
# REPEATED HANDLER
###################################################
@router.on_event("startup")
@repeat_every(seconds=600)  # 1 hour
def startup_event():
    refresh_event()
    