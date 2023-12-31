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

import os
import requests
import json
import logging

import pandas as pd
from typing import List

from .configuration import settings
# from .orion_utils import *

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson
from ..iot_platform import cosmicswamp as cosmicswamp


from typing import Any, Dict, AnyStr, List, Union

JSONStructure = Union[Dict[str, Any], List[Any]]

# Define Usual Router requirement
router = APIRouter(
    prefix="/simulation_platform/pcse_simulator",
    tags=["simulation_platform:pcse_simulator"],
    dependencies=[Depends(settings), Depends(orion.required_headers)]
)

@router.get("/")
def root():
    return "PCSE Simulator"

@router.get("/status")
def status():
    return {"status": "OK"}

# How do we make pcse_simulator publish to a seperate service_path.
@router.get("/remove_session")
def remove_session(request: Request):
    if "simulation" not in request.headers["Fiware-Servicepath"]:
        return 
    
    cosmicswamp.clear_session(request)


@router.get("/create_session")
def create_session(request: Request, simulation_tag: str):

    simrequest = orion.session(request.headers["Fiware-Service"], 
                               request.headers["Fiware-Servicepath"] + "_simulation_" + simulation_tag)
    remove_session(simrequest)

    # Now we get all entities from one entity, and we push it into the other.
    entities = cosmicswamp.get_all_current_entity_ids(request)

    for e in entities:
        entity_id = e["id"]
        entity_type = e["type"]
        entity_full = cosmicswamp.get_current_entity_from_id(request, entity_id)
        entity_full = ngsi.coerce_data(entity_full)
        cosmicswamp.create_entity(simrequest, entity_id, entity_type, jsondata=entity_full)
        
    return simrequest

                      


    
def get_simulation_for_zone_on_day(session, zone, date):

    coords = zone["location"]

    max_date = pd.to_datetime(date)
    min_date = max_date - dt.timedelta(days = max_days)
    date_range = [min_date.isoformat(),max_date.isoformat()]

    # Retrieve crop and soil for zone
    query = cosmicswamp.get_series_data_for_all_entities_of_type
    crops   = query(session, "Crop", attrs="*", date_range=date_range, ascending=False)
    soil    = query(session, "Soil", attrs="*", date_range=date_range, ascending=False)
    weather = query(session, "WeatherStation", attrs="*", date_range=date_range, ascending=False)


    # Retrieve 