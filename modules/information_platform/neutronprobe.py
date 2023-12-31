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

import pandas as pd
from typing import List

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson
import dependencies.log_utils as log

from .configuration import settings
import modules.iot_platform.cosmicswamp as cosmicswamp
from typing import Any, Dict, AnyStr, List, Union
from pydantic import BaseModel

JSONStructure = Union[Dict[str, Any], List[Any]]

################################################
# Routes
################################################
router = APIRouter(
    prefix="/information-platform/neutronprobe",
    tags=["information-platform:neutronprobe"],
    dependencies=[Depends(settings), Depends(orion.required_headers)]
)
router.verbosity = log.INFO

################################################
# Parameter Helpers
################################################
def MessageIndex(value): return orion.Number(value)
def UltralightMessage(value): return orion.String(value)
def NeutronCountsRaw(value): return orion.Number(value)
def NeutronRateRaw(value, unit="Hz"): return orion.Number(value)
def NeutronCountsCalibrated(value): return orion.Number(value)
def DryNeutronCountsCalibrated(value): return orion.Number(value)
def NeutronRateCalibrated(value, unit="Hz"): return orion.Number(value)
def AirPressure(value, unit="hPa"): return orion.Number(value, unit)
def AirTemperature(value, unit="C"): return orion.Number(value, unit)
def AirHumidity(value, unit="hPa"): return orion.Number(value, unit)
def TubePressure(value, unit="V"): return orion.Number(value, unit)
def TubeTemperature(value, unit="C"): return orion.Number(value, unit)
def TubeHumidity(value, unit="%"): return orion.Number(value, unit)
def BatteryVoltage(value, unit="V"): return orion.Number(value, unit)
def TimestampYYMMDDhhmm(value): return orion.Int(value)
def TimestampUnix(value): return orion.Int(value)
def SoilMoistureCentral(value): return orion.Number(value)
def SoilMoistureLow(value): return orion.Number(value)
def SoilMoistureHigh(value): return orion.Number(value)
def PressureCorrection(value): return orion.Number(value)
def HumidityCorrection(value): return orion.Number(value)
def CosmicCorrection(value): return orion.Number(value)

################################################
# Device Mappings
################################################
mqtt_mapping = {
    "I":   ["messageIndex", MessageIndex],
    "T0":  ["neutronCountsRaw", NeutronCountsRaw],
    "C0":  ["neutronCountsCalibrated", NeutronCountsCalibrated],
    "SM":  ["soilMoistureCentral", SoilMoistureCentral],
    "SL":  ["soilMoistureLow", SoilMoistureLow],
    "SH":  ["soilMoistureHigh", SoilMoistureHigh]
}

################################################
# Calibrations
################################################
import numpy as np
import scipy
def theta_value(N, N0, f, pb, extra):
    a0 = 0.0869 
    a1 = 0.3720
    a2 = 0.1236

    theta = ((a0/((f*N/N0)-a1)) - a2) + extra

    return theta

def calibrate_data_forward(session, entity_id, body):

    N0 = body["dryNeutronCountsCalibrated"]["value"]
    N = body["neutronCountsRaw"]["value"]

    f = 1.0
    pb = 1.2
    extra = 0.1

    sm = theta_value(N,N0,f,pb,extra)

    ngsi.set_value(body, "soilMoistureCentral", SoilMoistureCentral(sm))
    log.debug(router,"DATA FORWARD IN THETA ", N, sm)
    return body

def calibrate_data_backward(session, entity_id, body):

    sm = body["soilMoistureCentral"]["value"]

    N0 = body["dryNeutronCountsCalibrated"]["value"]
    Ns = np.linspace(N0*(0.4),N0, 30)

    f = 1.0
    pb = 1.2
    extra = 0.1

    thetas = theta_value(Ns,N0,f,pb,extra)
    func = scipy.interpolate.interp1d(thetas, Ns)
    n0 = func(sm)

    ngsi.set_value(body, "neutronCountsRaw", NeutronCountsRaw(n0))

    return body


################################################
# ROUTES
################################################

# -----------------------------------
# Device creation routine.
#
@router.get("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    time_index: str = None,
                    location: JSONStructure = None,
                    center_location: list = None,
                    radius: float = 200,
                    i0: int = 0,
                    c0: int = 0,
                    cc0: int = 0,
                    smc0: float = 0.0,
                    sml0: float = 0.0,
                    smh0: float = 0.0,
                    nd0: int = 2000,
                    jsondata: JSONStructure = None
    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    entity_type = "NeutronProbe"
    body = ngsi.compile_entity(jsondata, entity_id, entity_type, time_index, [])

    # Entity header variables
    orion.set_state_source(body, "CREATION", "API")
    print(body)
    ngsi.set_default(body, "location",      location)
    ngsi.set_default(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_default(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_default(body, "messageindex",     MessageIndex(i0))
    ngsi.set_default(body, "neutronCountsRaw", NeutronCountsRaw(c0))
    ngsi.set_default(body, "neutronCountsCalibrated", NeutronCountsCalibrated(cc0))
    ngsi.set_default(body, "dryNeutronCountsCalibrated", DryNeutronCountsCalibrated(nd0))

    ngsi.set_default(body, "soilMoistureCentral", SoilMoistureCentral(smc0))
    ngsi.set_default(body, "soilMoistureLow", SoilMoistureLow(sml0))
    ngsi.set_default(body, "soilMoistureHigh", SoilMoistureHigh(smh0))

    ngsi.set_default(body, "radius", orion.Number(radius))

    # Inferred location
    if not location and not center_location:
        center_location = [0.0,0.0]

    if radius and center_location:
        body["location"] = geojson.circle_around_point(geojson.point(center_location), radius, nsegments=24)

    log.debug(router,"CREATING", body)

    print(body, i0, MessageIndex(i0))

    cosmicswamp.create_entity(request, entity_id, entity_type, jsondata=body)

    return body


# -----------------------------------
# Device update routine.
# 
# Allows simulated or real data uploads
@router.post("/up/{entity_id}")
def update(request: Request,
                    entity_id,                      # Device Entity in Orion
                    attrs: List[str] = None,        # Additional custom attributes
                    time_index: str = None,
                    location: JSONStructure = None,
                    center_location: list = None,
                    radius: float = 200,
                    i0: int = 0,
                    c0: int = None,
                    cc0: int = None,
                    smc0: float = None,
                    sml0: float = None,
                    smh0: float = None,
                    nd0: int = None,
                    jsondata: JSONStructure = None,

    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    entity_type = "NeutronProbe"
    body = cosmicswamp.compile_entity_state_at_time(request, entity_id, entity_type, time_index, attrs, jsondata)

    # Entity header variables
    orion.set_state_source(body, "CREATION", "API")
    ngsi.set_value(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_value(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_value(body, "messageindex",     MessageIndex(i0))
    ngsi.set_value(body, "neutronCountsRaw", NeutronCountsRaw(c0))
    ngsi.set_value(body, "neutronCountsCalibrated", NeutronCountsCalibrated(cc0))
    ngsi.set_value(body, "dryNeutronCountsCalibrated", DryNeutronCountsCalibrated(nd0))

    ngsi.set_value(body, "soilMoistureCentral", SoilMoistureCentral(smc0))
    ngsi.set_value(body, "soilMoistureLow", SoilMoistureLow(sml0))
    ngsi.set_value(body, "soilMoistureHigh", SoilMoistureHigh(smh0))

    ngsi.set_value(body, "radius", orion.Number(radius))

    if not location and not center_location:
        center_location = [0.0,0.0]

    if radius and center_location:
        body["location"] = geojson.circle_around_point(geojson.point(center_location), radius, nsegments=24)

    if location:
        body["location"] = {}
        body["location"]["value"] = location
    
    # Final commit of new NGSI quantity
    if not cosmicswamp.has_current_entity_from_id(request, entity_id):
        cosmicswamp.create_entity(request, entity_id, entity_type, jsondata=body)
    else:
        cosmicswamp.update_entity(request, entity_id, entity_type, jsondata=body)        


@router.post("/iotagent/{entity_id}")
def iotagent(request: Request,
            entity_id,
            time_index: str = None,
            payload_type: str = None,
            payload_data: JSONStructure = None):
    
    # Parsing routines
    # - Thingsboard MQTT TTN Parser based on decoded_payload
    headers = orion.get_fiware_headers(request)
    body = cosmicswamp.compile_entity_state_at_time(request, entity_id, "NeutronProbe", time_index, None, None)

    if not cosmicswamp.has_current_entity_from_id(request, entity_id):
        body = create(request, entity_id)

    if payload_type == "mqtt_ttn":
        orion.set_state_source(body, "RAW", "TTN_MQTT")

        payload_data = json.loads(payload_data["payload_data"])

        if "uplink_message" not in payload_data: 
            return 

        # Add Raw UL
        ulstring = payload_data["uplink_message"]["decoded_payload"]["ultralight"]
        ngsi.set_value(body, "ultralight", UltralightMessage(ulstring))

        # Add Mapped Values
        ul = payload_data["uplink_message"]["decoded_payload"]["ngsi"]
        for key in mqtt_mapping:
            if key in ul: 
                ngsi.set_value(body, mqtt_mapping[key][0], mqtt_mapping[key][1](ul[key]))
        
        for key in ul:
            if key not in mqtt_mapping:
                log.error(router, "WARNING key is missing from mqtt_mapping : ", key)

        # -- Raw data needs to be calibrated
        print("NEUTRON BODY", body)

        if "dryNeutronCountsCalibrated" not in body: 
            body["dryNeutronCountsCalibrated"] = DryNeutronCountsCalibrated(2000)
            body["neutronCountsRaw"] = NeutronCountsRaw(2000)

        body = calibrate_data_forward(request, entity_id, body)
        orion.set_state_source(body, "CALIBRATED", "TTN_MQTT")

    print("IoT Message Data", headers, body)
    update(request, entity_id, time_index=time_index, jsondata=body)

    return body

# -----------------------------------
# Device simulation routine.
# 
# Simulates raw moisture ADC readings based on selected
# true soil moisture values at a specific time.
@router.post("/simulate/{entity_id}")
def simulate(request: Request,
                    entity_id,                    
                    time_index: str = None,
                    location: List[float] = None,
                    i0: int = None,
                    c0: int = None,
                    sc0: int = None,
                    smc0: float = None,
                    nd0: float = None,
                    ap: float = None,
                    at: float = None,
                    ah: float = None
                    ):
    
    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    entity_type = "NeutronProbe"
    body = cosmicswamp.compile_entity_state_at_time(request, entity_id, entity_type, time_index, attrs=None, jsondata=None)

    # Entity header variables
    orion.set_state_source(body, "SIMULATED", "API")
    ngsi.set_override(body, "location",      location)
    ngsi.set_override(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_override(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_override(body, "messageindex",            MessageIndex(i0))
    ngsi.set_override(body, "neutronCountsRaw",        NeutronCountsRaw(c0))
    ngsi.set_override(body, "neutronCountsCalibrated", NeutronCountsCalibrated(sc0))
    ngsi.set_override(body, "dryNeutronCountsCalibrated",        DryNeutronCountsCalibrated(nd0))
    ngsi.set_override(body, "soilMoistureCentral",     SoilMoistureCentral(smc0))

    # Calibration Routines
    # - We calibrate backwards every possible value of the three depth gauge
    body = calibrate_data_backward(request, entity_id, body)

    # Smearing Routines
    # - Introduce random smearing to simulated raw data
    log.debug(router,"Neutron Counts", body["neutronCountsRaw"])
    raw_value = body["neutronCountsRaw"]["value"]
    raw_shift = np.random.normal(0.0, np.sqrt(raw_value))
    ngsi.set_override(body, "neutronCountsRaw", raw_value + raw_shift)

    # for i in range(3):
            
    #     raw_value = body[f"soilmoistureraw{i}"]["value"]
    #     raw_shift = np.random.uniform(0.0, adc_noise) + adc_offset

    #     ngsi.set_override(body, f"soilmoistureraw{i}", raw_value + raw_shift)
        
    # - After smearing we have to calibrate forward again
    body = calibrate_data_forward(request, entity_id, body)

    # Submit to ORION/CRATE
    cosmicswamp.update_entity(request, entity_id, entity_type, jsondata=body)