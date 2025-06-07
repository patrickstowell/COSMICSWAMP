from fastapi import FastAPI, Header, Request, APIRouter, Depends, HTTPException, Query
from fastapi_utils.tasks import repeat_every

from typing import Union, Annotated, List, Any, Dict, AnyStr, Union
JSONStructure = Union[Dict[str, Any], List[Any]]
import matplotlib.pyplot as plt
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

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson

import modules.iot_platform.cosmicswamp as cosmicswamp

import modules.information_platform.configuration as configuration
import modules.information_platform.managementzone as managementzone
import modules.information_platform as information_platform
from pcse.db import NASAPowerWeatherDataProvider

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
import concurrent

################################################
# MODULE ROUTER
################################################
router = APIRouter(
    prefix="/fusion-platform/zone-fusion",
    tags=["fusion-platform:zone-fusion"],
    dependencies=[Depends(configuration.settings), Depends(orion.required_headers)]
)
################################################
# PARAMETER DEFINITIONS
################################################
def MessageIndex(value):                         return orion.Int(value)

def to_unix(dt):
    return float(time.mktime(dt.timetuple()))

def run_pcse_member(member, day):
    member.run_till(day)

def run_pcse_member_one_day(member):
    member.run()

################################################
# ROUTES CREATE/UP/DELETE
################################################
@router.get("/average/{entity_id}")
def average_zone(request: Request,
                    entity_id,
                    time_end: str = None,
                    time_start: str = None
    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_end)
    time_index_end = orion.infer_timestamp(time_end)
    time_index_start = orion.infer_timestamp(time_start)



    # Get Default Parameters
    # zone = cosmicswamp.compile_entity_state_at_time(request, entity_id, "ManagementZone", time_index, attrs=[], jsondata={})
    # print("ENTITY", entity_id)
    zone = cosmicswamp.get_current_entity_from_id(request, entity_id)
    print(zone)
    for key in zone:
        print(key)
    zoneid = zone["zoneid"]["value"]
    zone_location = zone["location"]["value"]

    # Get Crop data for zone
    agros = cosmicswamp.get_entities_by_type_and_geometry(request, "Agronomy", geojson.to_wgs84_list(zone_location["coordinates"]))
    crops = cosmicswamp.get_entities_by_type_and_geometry(request, "Crop", geojson.to_wgs84_list(zone_location["coordinates"]))
    soils = cosmicswamp.get_entities_by_type_and_geometry(request, "Soil", geojson.to_wgs84_list(zone_location["coordinates"]))

    avg_agro = ngsi.mean(agros)
    avg_crop = ngsi.mean(crops)
    avg_soil = ngsi.mean(soils)

    # Make time series cuts
    time_high = to_unix(pd.to_datetime(time_index_end))
    time_low = to_unix(pd.to_datetime(avg_agro["start_date"]["value"]))

    # Get Time Series Weather Data since start of growing period
    print(request)

    print("WEATHER FUSION CHECK TESTING 2")
    weather_data = cosmicswamp.get_series_data_for_entity(request, "urn:ngsi-ld:WeatherStation:1", attrs=["time_index","airtemperature","airpressure","airhumidity","windspeed","winddirection","solarradiation","batteryvoltage","rainfall"], limit=100000, cuts=[f"time_index < {time_high}",f"time_index > {time_low}"])
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

        zone["avg_weather"] = orion.Structured(daily_data.to_dict())


    soildepthprobes = cosmicswamp.get_entities_by_type_and_geometry(request, "SoilDepthProbe", geojson.to_wgs84_list(zone_location["coordinates"]))
    soilprobedata = []
    for probe in soildepthprobes:
        probe_data = cosmicswamp.get_series_data_for_entity(request, probe["id"], attrs=["time_index", "soilmoisturecalibrated0","soilmoisturecalibrated1","soilmoisturecalibrated2"], limit=100000, cuts=[f"time_index < {time_high}",f"time_index > {time_low}"])
        data = pd.DataFrame(data=(probe_data))

        data["date"] = pd.to_datetime(data["time_index"], unit="ms")
        data["day"]  = data["date"].dt.date
        hourly_data = data[["day", "soilmoisturecalibrated0","soilmoisturecalibrated1","soilmoisturecalibrated2"]]

        daily_data = hourly_data.groupby("day").mean().reset_index()
        daily_data["day"] = pd.to_datetime(daily_data["day"]).dt.date

        if len(soilprobedata) == 0: soilprobedata = daily_data
        else: soilprobedata = pd.concat([soilprobedata, daily_data])

    neutronprobes = cosmicswamp.get_entities_by_type_and_geometry(request, "NeutronProbe", geojson.to_wgs84_list(zone_location["coordinates"]))
    neutronprobedata = []
    for probe in neutronprobes:
        probe_data = cosmicswamp.get_series_data_for_entity(request, probe["id"], attrs=["time_index", "soilmoisturecentral"], limit=100000, cuts=[f"time_index < {time_high}",f"time_index > {time_low}"])
        data = pd.DataFrame(data=(probe_data))

        data["date"] = pd.to_datetime(data["time_index"], unit="ms")
        data["day"]  = data["date"].dt.date
        hourly_data = data[["day", "soilmoisturecentral"]]

        daily_data = hourly_data.groupby("day").mean().reset_index()

        daily_data["day"] = pd.to_datetime(daily_data["day"]).dt.date

        if len(neutronprobedata) == 0: neutronprobedata = daily_data
        else: neutronprobedata = pd.concat([neutronprobedata, daily_data])


    del avg_agro["location"]
    del avg_soil["location"]

    # zone["avg_agro"] = orion.Structured(avg_agro)
    # zone["avg_crop"] = orion.Structured(avg_crop)
    # zone["avg_soil"] = orion.Structured(avg_soil)


    print("DATASETS")
    print(weather_df)
    print(soilprobedata)
    print(neutronprobedata)

    zone["zoneid"]["type"] = "Text"


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
    weather_df["TEMP"] = weather_df["airtemperature"]
    weather_df["TMIN"] = weather_df["airtemperature"]
    weather_df["TMAX"] = weather_df["airtemperature"]

    # averaged_weather_provider = PandasWeatherDataProviderForecastingModel(weather_df, longitude=longitude, latitude=latiude)
    averaged_weather_provider = information_platform.weatherstation.PandasWeatherDataProvider(weather_df, elevation=60, longitude=longitude, latitude=latiude)

    # for key in df:
    #     print("WDP KEY", key)
    # print("WDP DF", df.SM)
    # if len(df.SM) > 10 and len(neutronprobedata) > 0:
    #     plt.plot(df.day, df.SM)
    #     plt.plot(neutronprobedata.day, neutronprobedata.soilmoisturecentral)
    #     plt.show()

    # Use ensemble inference to reconfigure model based on SM data from neutron probe
        
        # A container for the parameters that we will override
    print(neutronprobedata)

    if len(neutronprobedata) > 1:
        
        states_for_DA = ["SM", "WST", "WSO"]
        observed_states = ["SM"]

        dates_of_observation = []
        observed_lai = []
        std_lai = []
        for i in range(len(neutronprobedata)):
            dates_of_observation.append(neutronprobedata.day[i])
            observed_lai.append(neutronprobedata.soilmoisturecentral[i])
            std_lai.append(0.05*neutronprobedata.soilmoisturecentral[i])

        observations_for_DA = []
        observations_for_DA = [(d, {"SM": (lai, errlai)}) for d, lai, errlai, in zip(dates_of_observation, observed_lai, std_lai)]

        ensemble_size = 100
        np.random.seed(10000)
        override_parameters = {}

        #Initial conditions
        override_parameters["SOPE"] = np.random.normal(150., 50., (ensemble_size))
        override_parameters["WAV"] = np.random.normal(30, 5, (ensemble_size))
        # parameters
        override_parameters["KSUB"] = np.random.normal(31, 3 ,(ensemble_size))
        override_parameters["SMFCF"] = np.random.normal(0.31, 0.03 ,(ensemble_size))
        ensemble = []
        for i in range(ensemble_size):
            p = pcse.util.copy.deepcopy(parameter_provider)
            for par, distr in override_parameters.items():
                p.set_override(par, distr[i])
            member = Wofost72_WLP_FD(p, averaged_weather_provider, agro_provider)
            ensemble.append(member)

        day, obs = observations_for_DA.pop(0)
        while len(observations_for_DA) > 0:

            day, obs = observations_for_DA.pop(0)

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                # List to store Future objects representing the running tasks
                futures = []

                # Submit the tasks to the executor
                for member in ensemble:
                    future = executor.submit(run_pcse_member, (member, day))
                    futures.append(future)

                # Wait for all tasks to complete
                concurrent.futures.wait(futures)

            print("Ensemble now at day %s" % member.day, day)
            print("%s observations left!" % len(observations_for_DA))


            collected_states = []
            for member in ensemble:
                t = {}
                for state in states_for_DA:
                    t[state] = member.get_variable(state)
                collected_states.append(t)
            df_A = pd.DataFrame(collected_states)
            A = np.matrix(df_A).T
            P_e = np.matrix(df_A.cov())



            perturbed_obs = []
            for state in observed_states:
                (value, std) = obs[state]
                d = np.random.normal(value, std, (ensemble_size))
                perturbed_obs.append(d)
            df_perturbed_obs = pd.DataFrame(perturbed_obs).T
            df_perturbed_obs.columns = observed_states
            D = np.matrix(df_perturbed_obs).T  # Perturbed observations
            R_e = np.matrix(df_perturbed_obs.cov())  # Covariance


            H = np.matrix([1.,0.,0.])
            K1 = P_e * (H.T)
            K2 = (H * P_e) * H.T
            K = K1 * ((K2 + R_e).I)


            # Here we compute the analysed states
            Aa = A + K * (D - (H * A))
            df_Aa = pd.DataFrame(Aa.T, columns=states_for_DA)

            for member, new_states in zip(ensemble, df_Aa.itertuples()):
                member.set_variable("SM", new_states.SM)
                member.set_variable("WST", new_states.WST)
                member.set_variable("WSO", new_states.WSO)



        results = [pd.DataFrame(member.get_output()).set_index("day").tail(1) for member in ensemble]

        combineddf = pd.concat(results)
        combineddf = combineddf.reset_index()

        meandf = combineddf.groupby("day").quantile(0.5)
        mindf = combineddf.groupby("day").quantile(0.25)
        maxdf = combineddf.groupby("day").quantile(0.75)

        meandf.reset_index(inplace=True)
        maxdf.reset_index(inplace=True)
        mindf.reset_index(inplace=True)

        df = meandf
        df["day"] = pd.to_datetime(df.day)
        df["unix"] = df["day"].astype(int) / 10**9

        row = df.tail(1)
        zone["leafAreaIndex"] = orion.Number(row.LAI.values)
        zone["rootDepth"] = orion.Number(row.RD.values)
        zone["rootMoistureEstimate"] = orion.Number(row.SM.values)
        zone["aboveGroundBiomass"] = orion.Number(row.TAGP.values)
        zone["weightOrgans"] = orion.Number(row.TWLV.values)
        zone["weightLeaves"] = orion.Number(row.SM.values)
        zone["weightStems"] = orion.Number(row.TWST.values)
        zone["weightRoots"] = orion.Number(row.TWRT.values)
        zone["cropRadiationAbsorbed"] = orion.Number(row.TRA.values)

        row = mindf.tail(1)
        zone["leafAreaIndexlow"] = orion.Number(row.LAI.values)
        zone["rootDepthlow"] = orion.Number(row.RD.values)
        zone["rootMoistureEstimatelow"] = orion.Number(row.SM.values)
        zone["aboveGroundBiomasslow"] = orion.Number(row.TAGP.values)
        zone["weightOrganslow"] = orion.Number(row.TWLV.values)
        zone["weightLeaveslow"] = orion.Number(row.SM.values)
        zone["weightStemslow"] = orion.Number(row.TWST.values)
        zone["weightRootslow"] = orion.Number(row.TWRT.values)
        zone["cropRadiationAbsorbedlow"] = orion.Number(row.TRA.values)

        row = maxdf.tail(1)
        zone["leafAreaIndexhigh"] = orion.Number(row.LAI.values)
        zone["rootDepthhigh"] = orion.Number(row.RD.values)
        zone["rootMoistureEstimatehigh"] = orion.Number(row.SM.values)
        zone["aboveGroundBiomasshigh"] = orion.Number(row.TAGP.values)
        zone["weightOrganshigh"] = orion.Number(row.TWLV.values)
        zone["weightLeaveshigh"] = orion.Number(row.SM.values)
        zone["weightStemshigh"] = orion.Number(row.TWST.values)
        zone["weightRootshigh"] = orion.Number(row.TWRT.values)
        zone["cropRadiationAbsorbedhigh"] = orion.Number(row.TRA.values)

        zone["STATE"] = orion.String("FUSION")
        zone["TimeInstant"] = orion.TimeInstant(time_index)
        zone["ForecastInstant"] = orion.TimeInstant(time_index)

        managementzone.update(request, entity_id, time_index=time_index, jsondata=zone)

        # nsteps = 0
        # while True:
        #     nsteps += 1


        #     with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        #         # List to store Future objects representing the running tasks
        #         futures = []

        #         # Submit the tasks to the executor
        #         for member in ensemble:
        #             future = executor.submit(run_pcse_member_one_day, member)
        #             futures.append(future)

        #         # Wait for all tasks to complete
        #         concurrent.futures.wait(futures)

        #     results = [pd.DataFrame(member.get_output()).set_index("day").tail(1) for member in ensemble]

        #     combineddf = pd.concat(results)
        #     combineddf = combineddf.reset_index()

        #     meandf = combineddf.groupby("day").quantile(0.5)
        #     mindf = combineddf.groupby("day").quantile(0.25)
        #     maxdf = combineddf.groupby("day").quantile(0.75)

        #     meandf.reset_index(inplace=True)
        #     maxdf.reset_index(inplace=True)
        #     mindf.reset_index(inplace=True)

        #     df = meandf
        #     df["day"] = pd.to_datetime(df.day)
        #     df["unix"] = df["day"].astype(int) / 10**9

        #     row = df.tail(1)
        #     zone["leafAreaIndex"] = orion.Number(row.LAI.values)
        #     zone["rootDepth"] = orion.Number(row.RD.values)
        #     zone["rootMoistureEstimate"] = orion.Number(row.SM.values)
        #     zone["aboveGroundBiomass"] = orion.Number(row.TAGP.values)
        #     zone["weightOrgans"] = orion.Number(row.TWLV.values)
        #     zone["weightLeaves"] = orion.Number(row.SM.values)
        #     zone["weightStems"] = orion.Number(row.TWST.values)
        #     zone["weightRoots"] = orion.Number(row.TWRT.values)
        #     zone["cropRadiationAbsorbed"] = orion.Number(row.TRA.values)

        #     row = mindf.tail(1)
        #     zone["leafAreaIndexlow"] = orion.Number(row.LAI.values)
        #     zone["rootDepthlow"] = orion.Number(row.RD.values)
        #     zone["rootMoistureEstimatelow"] = orion.Number(row.SM.values)
        #     zone["aboveGroundBiomasslow"] = orion.Number(row.TAGP.values)
        #     zone["weightOrganslow"] = orion.Number(row.TWLV.values)
        #     zone["weightLeaveslow"] = orion.Number(row.SM.values)
        #     zone["weightStemslow"] = orion.Number(row.TWST.values)
        #     zone["weightRootslow"] = orion.Number(row.TWRT.values)
        #     zone["cropRadiationAbsorbedlow"] = orion.Number(row.TRA.values)

        #     row = maxdf.tail(1)
        #     zone["leafAreaIndexhigh"] = orion.Number(row.LAI.values)
        #     zone["rootDepthhigh"] = orion.Number(row.RD.values)
        #     zone["rootMoistureEstimatehigh"] = orion.Number(row.SM.values)
        #     zone["aboveGroundBiomasshigh"] = orion.Number(row.TAGP.values)
        #     zone["weightOrganshigh"] = orion.Number(row.TWLV.values)
        #     zone["weightLeaveshigh"] = orion.Number(row.SM.values)
        #     zone["weightStemshigh"] = orion.Number(row.TWST.values)
        #     zone["weightRootshigh"] = orion.Number(row.TWRT.values)
        #     zone["cropRadiationAbsorbedhigh"] = orion.Number(row.TRA.values)


        #     zone["STATE"] = orion.String("FORECAST")
        #     zone["TimeInstant"] = orion.TimeInstant((pd.to_datetime(time_index) + datetime.timedelta(days=nsteps)).isoformat())
        #     zone["ForecastInstant"] = orion.TimeInstant(time_index)
        #     print("Forecasted : ", zone["TimeInstant"])

        #     cur_time = pd.to_datetime( zone["TimeInstant"]["value"] )
        #     cut_time_end = (pd.to_datetime(avg_agro["end_date"]["value"]))

        #     if cur_time > cut_time_end: break

        #     managementzone.update(request, entity_id, time_index=(pd.to_datetime(time_index) + datetime.timedelta(days=nsteps)).isoformat(), jsondata=zone)

    print("ManagementZone Finished for the day")






        # Now run the ensembles to the end of the growing cycle, and upload a new zone 
    

    # Finally run ensemble fusion using forecast data for the current model
    # wofost.run_till_terminate()


    return zone

################################################
# REGULAR FUSION
################################################
# @router.on_event("startup")
# @repeat_every(seconds=3600*24)  
def process_all_zones_in_platform(time_end=datetime.datetime.now(), time_start=None):

    session_list = cosmicswamp.get_session()
    for pathcombo in session_list["sessions"]["value"]:
        service, servicepath = pathcombo.split("/")
        session = orion.session(service,"/" + servicepath)

        if servicepath != "new_session": continue
        zones = cosmicswamp.get_all_current_entities_of_type(session, "ManagementZone")
        for zone in zones:
            average_zone(session, zone["id"], time_end, time_start)