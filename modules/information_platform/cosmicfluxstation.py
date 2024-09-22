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

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson

import modules.iot_platform.cosmicswamp as cosmicswamp

import modules.information_platform.configuration as configuration
import modules.information_platform.managementzone as managementzone

###################################################
# ENTITY MODEL : CosmicFluxStation
###################################################
ENTITY_TYPE = "CosmicFluxStation"
ENTITY_TYPE_lower = ENTITY_TYPE.lower()


################################################
# MODULE ROUTER
################################################
router = APIRouter(
    prefix="/information-platform/cosmicfluxstation",
    tags=["information-platform","cosmicfluxstation"],
    dependencies=[Depends(configuration.settings), Depends(orion.required_headers)]
)


################################################
# PARAMETER DEFINITIONS
################################################
def MessageIndex(value): return orion.Int(value)
def RequestStatus(value): return orion.String(value)
def NMDBStation(value): return orion.String(value)
def NMDBBaseline(value): return orion.Number(value)
def Intensity(value): return orion.Number(value)

################################################
# HELPER FUNCTION
################################################
def GetNMDBData(start_date, end_date, station="JUNG", baseline=145):

    station_list = f"stations%5B%5D={station}"
    
    # Main NEST Interface Call
    stday = start_date.day
    stmon = start_date.month
    styea = start_date.year
    sthou = start_date.hour
    stmin = start_date.minute
    
    enday = end_date.day
    enmon = end_date.month
    enyea = end_date.year
    enhou = end_date.hour
    enmin = end_date.minute

    url=f"http://nest.nmdb.eu/draw_graph.php?feorce=1&wget=1&{station_list}&output=ascii&tabchoice=ori&dtype=corr_for_efficiency&date_choice=bydate&start_day={stday}&start_month={stmon}&start_year={styea}&start_hour={sthou}&start_min={stmin}&end_day={enday}&end_month={enmon}&end_year={enyea}&end_hour={enhou}&end_min={enmin}&yunits=0&tresolution=15"

    print(url)
    res = requests.get(url)
        
    print("REST CALL", res, res.status_code)
    if (res.status_code == 200):

        data = res.text
        data = data.split("\n")
        data = data[24:]
        data = data[0:-4] 
        print(data)
        print("ENEUMRATE")

        datadict = {
            "TimeInstant": [],
            "currentintensity": [],
            "relativeintensity": [],
            "baselineintensity": []
        }

        print("DATA", data)
        for entry in data:
            date = pd.to_datetime(entry.split(";")[0])
            value =  float(entry.split(";")[1])

            datadict["TimeInstant"].append(date.isoformat())
            datadict["currentintensity"].append(value)
            datadict["relativeintensity"].append(value/baseline)
            datadict["baselineintensity"].append(value/baseline)

        print(datadict)
        return pd.DataFrame(data=datadict)
    
    return []

    

################################################
# ROUTES CREATE/UP/DELETE
################################################
@router.get("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    time_index: str = None,
                    location: JSONStructure = None,
                    jsondata: JSONStructure = None,
                    status: str = "CREATE",
                    nmdbstation: str = None,
                    nmdbbaseline: float = None,
                    currentintensity: float = None,
                    relativeintensity: float = None,
                    baselineintensity: float = None
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
    ngsi.set_default(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_default(body, "nmdbstation", orion.String(nmdbstation))
    ngsi.set_default(body, "nmdbbaseline", NMDBBaseline(nmdbbaseline))
    ngsi.set_default(body, "status", RequestStatus(status))
    ngsi.set_override(body, "currentintensity", Intensity(currentintensity))
    ngsi.set_override(body, "relativeintensity", Intensity(relativeintensity))
    ngsi.set_override(body, "baselineintensity", Intensity(baselineintensity))

    cosmicswamp.create_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)

    return body

@router.get("/update/{entity_id}")
def update(request: Request,
                    entity_id,
                    time_index: str = None,
                    location: JSONStructure = None,
                    jsondata: JSONStructure = None,
                    status: str = None,
                    nmdbstation: str = None,
                    nmdbbaseline: float = None,
                    currentintensity: float = None,
                    relativeintensity: float = None,
                    baselineintensity: float = None
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
    ngsi.set_override(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_override(body, "nmdbstation", NMDBStation(nmdbstation))
    ngsi.set_override(body, "nmdbbaseline", NMDBBaseline(nmdbbaseline))
    ngsi.set_override(body, "currentintensity", Intensity(currentintensity))
    ngsi.set_override(body, "relativeintensity", Intensity(relativeintensity))
    ngsi.set_override(body, "baselineintensity", Intensity(baselineintensity))

    ngsi.set_override(body, "status", RequestStatus(status))

    cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    return body


@router.get("/refresh")
def refresh_event(time_end=datetime.datetime.now(), time_start=None):
    """
    Loops over available COSMIC STATION
    """    

    time_end = pd.to_datetime([time_end])[0]
    if not time_start:
        time_start = time_end - datetime.timedelta(hours=24)
    else:
        time_start = pd.to_datetime([time_end])[0]
        
    # Sessions need to be run for all possible maps.
    session_list = cosmicswamp.get_session()
    for pathcombo in session_list["sessions"]["value"]:
        service, servicepath = pathcombo.split("/")
        session = orion.session(service,"/" + servicepath)

        # Get Weather Forecasts
        stations = cosmicswamp.get_all_current_entities_of_type(session, "CosmicFluxStation")
        for wf in stations:

            station = wf["nmdbstation"]["value"]
            baseline = wf["nmdbbaseline"]["value"]

            df = GetNMDBData(time_start, time_end, station, baseline)

            if len(df) == 0: 
                update(session, wf["id"], status="FAILED" )
                continue

            print(df)

            body = wf
            for i in range(len(df)):
                row = df.iloc[i]

                print("ROW",row["TimeInstant"])
                wf["TimeInstant"] = orion.TimeInstant(row["TimeInstant"])
                wf["RequestInstant"] = orion.TimeInstant(row["TimeInstant"])

                wf["currentintensity"] = Intensity(row["currentintensity"])
                wf["relativeintensity"] = Intensity(row["relativeintensity"])
                wf["baselineintensity"] = Intensity(row["baselineintensity"])

                update(session, wf["id"], jsondata=body, time_index=wf["TimeInstant"]["value"], status="REQUESTED" )


###################################################
# REPEATED HANDLER
###################################################
@router.on_event("startup")
@repeat_every(seconds=3600)  # 1 hour
def startup_event():
    refresh_event()
    