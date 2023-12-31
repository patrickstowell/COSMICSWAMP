from fastapi import FastAPI, Header, Request, APIRouter, Depends, HTTPException, Query

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
import dependencies.log_utils as log

import modules.iot_platform.cosmicswamp as cosmicswamp

import modules.information_platform.configuration as configuration
import modules.information_platform.managementzone as managementzone

###################################################
# ENTITY MODEL : CalibrationMeasurement  # QUERY Calibration Meaesurements in Vicinity
###################################################
ENTITY_TYPE = "CalibrationMeasurement"
ENTITY_TYPE_lower = ENTITY_TYPE.lower()


################################################
# MODULE ROUTER
################################################
router = APIRouter(
    prefix="/information-platform/calibrationmeasurement",
    tags=["information-platform:calibrationmeasurement"],
    dependencies=[Depends(configuration.settings), Depends(orion.required_headers)]
)
router.verbosity = log.INFO

################################################
# PARAMETER DEFINITIONS
################################################
def MeasurementIndex(value):                         return orion.Int(value)
def MeasurementType(value): return orion.String(value)
def MeasurementLabel(value): return orion.String(value)
def MeasurementNumber(value): return orion.Number(value)
def MeasurementString(value): return orion.String(value)
def MeasurementObject(value): return orion.Structured(value)


################################################
# ROUTES CREATE/UP/DELETE
################################################
@router.get("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    time_index: str = None,
                    location: dict = None,
                    index: int = None,
                    type: str = None,
                    label: str = None,
                    number: float = None,
                    integer: int = None,
                    string: str = None,
                    object: dict = None
    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    body = ngsi.compile_entity({}, entity_id, ENTITY_TYPE, time_index, [])

    # Entity header variables
    orion.set_state_source(body, "CREATION", "API")
    ngsi.set_default(body, "location",      location)
    ngsi.set_default(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_default(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_default(body, "measurementindex",     MeasurementIndex(index))
    ngsi.set_default(body, "measurementtype", MeasurementType(type))
    ngsi.set_default(body, "measurementlabel", MeasurementLabel(label))
    ngsi.set_default(body, "measurementnumber", MeasurementNumber(number))
    ngsi.set_default(body, "measurementstring", MeasurementString(string))
    ngsi.set_default(body, "measurementobject", MeasurementObject(object))

    # Final commit of new NGSI quantity
    if not cosmicswamp.has_current_entity_from_id(request, entity_id):
        cosmicswamp.create_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    else:
        cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)

    return body


@router.post("/up/{entity_id}")
def update(request: Request,
                    entity_id,                      
                    time_index: str = None,
                    location: dict = None,
                    index: int = None,
                    type: str = None,
                    label: str = None,
                    number: float = None,
                    integer: int = None,
                    string: str = None,
                    object: dict = None
    ):
    
    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    body = ngsi.compile_entity({}, entity_id, ENTITY_TYPE, time_index, [])

    # Entity header variables
    orion.set_state_source(body, "UPDATED", "API")
    ngsi.set_override(body, "location",      location)
    ngsi.set_override(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_override(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_default(body, "measurementindex",  MeasurementIndex(index))
    ngsi.set_default(body, "measurementtype",   MeasurementType(type))
    ngsi.set_default(body, "measurementlabel",  MeasurementLabel(label))
    ngsi.set_default(body, "measurementnumber", MeasurementNumber(number))
    ngsi.set_default(body, "measurementstring", MeasurementString(string))
    ngsi.set_default(body, "measurementobject", MeasurementObject(object))

    # Final commit of new NGSI quantity
    if not cosmicswamp.has_current_entity_from_id(request, entity_id):
        cosmicswamp.create_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    else:
        cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
        