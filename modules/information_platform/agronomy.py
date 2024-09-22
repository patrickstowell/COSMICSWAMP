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

import os
import requests
import json
import logging
import yaml

import pandas as pd
from typing import List

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson

from .configuration import settings
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.information_platform.managementzone as managementzone

NULL_VALUE = -999
from typing import Any, Dict, AnyStr, List, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

# Define Usual Router requirement
router = APIRouter(
    prefix="/information-platform/agronomy",
    tags=["information-platform:agronomy"],
    dependencies=[Depends(settings), Depends(orion.required_headers)]
)

@router.get("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    time_index: str = None,
                    jsondata: JSONStructure = None,
                    location: dict = {},
                    end_date: str = "",
                    start_date: str = "", 
                    start_type: str="emergence",
                    end_type: str="harvest",
                    max_duration: int=300,
                    crop_name: str = "Unknown",
                    variety_name: str = "Unknown",
                    irrigation_application: dict = {},
                    nitrogen_application: dict = {}
                    ):

    headers = orion.get_fiware_headers(request)

    entity_type = "Agronomy"

    body = ngsi.compile_entity(jsondata, entity_id, entity_type, time_index, [])

    ngsi.set_default(body, "location", location)

    ngsi.set_default(body, "TimeInstant", orion.TimeInstant(time_index))

    ngsi.set_default(body, "start_date", orion.TimeInstant(start_date))
    ngsi.set_default(body, "end_date", orion.TimeInstant(end_date))
    ngsi.set_default(body, "max_duration", orion.Number(max_duration, "day"))
    ngsi.set_default(body, "start_type", orion.String(start_type))
    ngsi.set_default(body, "end_type", orion.String(end_type))

    ngsi.set_default(body, "crop_name",    orion.String(crop_name)    )
    ngsi.set_default(body, "variety_name", orion.String(variety_name) )

    ngsi.set_default(body, "irrigation_application", orion.Structured(irrigation_application) )
    ngsi.set_default(body, "nitrogen_application", orion.Structured(nitrogen_application) )

    cosmicswamp.create_entity(request, entity_id, jsondata=body)

    return body

def pcse_agro_from_ngsi(data):

    crop_name    = data["crop_name"]["value"]
    variety_name = data["variety_name"]["value"]


    start_date = pd.to_datetime([data["start_date"]["value"]])[0].date()
    end_date = pd.to_datetime([data["end_date"]["value"]])[0].date()
    start_type = data["start_type"]["value"]
    end_type = data["end_type"]["value"]
    max_duration = int(data["max_duration"]["value"])

    irrigation_application = data["irrigation_application"]["value"]

    yaml_agro = f"""    - {start_date}:
        CropCalendar:
          crop_name: {crop_name}
          variety_name: {variety_name}
          crop_start_date: {start_date}
          crop_start_type: {start_type}
          crop_end_date: {end_date}
          crop_end_type: {end_type}
          max_duration: {max_duration}
    """

    if irrigation_application != {}:

      yaml_agro += """
          StateEvents: null
          TimedEvents: 
          -   event_signal: irrigate
              name: Irrigation application table
              comment: All irrigation amounts in cm
              events_table:
      """

      keys = []
      for k in irrigation_application: keys.append(k)
      keys = sorted(keys)

      for k in keys:
        date = k
        amount = irrigation_application[k]["amount"]
        efficiency = irrigation_application[k]["efficiency"]
        yaml_agro += f"""
                - {date}: \{amount: {amount}, efficiency: {efficiency}\}
        """
    else:
        yaml_agro += """    StateEvents: null
        TimedEvents: null
        """

    agromanagement = yaml.safe_load(yaml_agro)
    return agromanagement
