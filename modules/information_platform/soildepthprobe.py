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
# ENTITY MODEL : SoilDepthProbe
###################################################
ENTITY_TYPE = "SoilDepthProbe"
ENTITY_TYPE_lower = ENTITY_TYPE.lower()


################################################
# MODULE ROUTER
################################################
router = APIRouter(
    prefix="/information-platform/soildepthprobe",
    tags=["soildepthprobe","information-platform"],
    dependencies=[Depends(configuration.settings), Depends(orion.required_headers)]
)
router.verbosity = log.DEBUG


################################################
# PARAMETER DEFINITIONS
################################################
def MessageIndex(value):                         return orion.Int(value)
def UltralightMessage(value):                    return orion.String(value)
def SoilTemperature(value, unit="C"):            return orion.Number(value, unit)
def SoilCapacitance(value, unit="ADC"):          return orion.Number(value, unit)
def SoilMoistureRaw(value, unit="ADC"):          return orion.Number(value, unit)
def SoilMoistureCalibrated(value, unit="m3/m3"): return orion.Number(value, unit)
def BatteryVoltage(value, unit="V"):             return orion.Number(value, unit)
def TimestampYYMMDDhhmm(value):                  return orion.Int(value)
def DeviceState(value):                          return orion.String(value)
def DeviceSource(value):                         return orion.String(value)

def CalibrationFuction(function=None, **kwargs):
    if not function: function = "a + b*x + c/x/x"
    constants = {}

    if not kwargs:
        constants = {
            "a": 2.5257E-01,
            "b": 2.5030E-04,
            "c": -4.5813E+03
        }

    for key in kwargs:
        constants[key] = kwargs[key]

    return orion.Structured({"function": function, "constants": constants})


################################################
# Device Mappings
################################################
mqtt_mapping = {
    "I":   ["messageIndex", MessageIndex],
    "T1":  ["soiltemperature0", SoilTemperature],
    "T2":  ["soiltemperature1", SoilTemperature],
    "T3":  ["soiltemperature2", SoilTemperature],
    "C1":  ["soilcapacitance0", SoilCapacitance],
    "C2":  ["soilcapacitance1", SoilCapacitance],
    "C3":  ["soilcapacitance2", SoilCapacitance],
    "M1":  ["soilmoistureraw0", SoilMoistureRaw],
    "M2":  ["soilmoistureraw1", SoilMoistureRaw],
    "M3":  ["soilmoistureraw2", SoilMoistureRaw],
    "SC1": ["soilmoisturecalibrated0", SoilMoistureCalibrated],
    "SC2": ["soilmoisturecalibrated1", SoilMoistureCalibrated],
    "SC3": ["soilmoisturecalibrated2", SoilMoistureCalibrated],
    "VB":  ["batteryvoltage", BatteryVoltage],
    "S":   ["timestampYYMMDDhhmm", TimestampYYMMDDhhmm]
}

################################################
# Calibrations
################################################
def calibrate_data_forward(session, entity_id, body):

    entity = cosmicswamp.get_current_entity_from_id(session, entity_id)

    for i in range(3):

        if (f"soilmoistureraw{i}" in body):

            if f"soilcalibration{i}" not in body:
                if f"soilcalibration{i}" in entity: body[f"soilcalibration{i}"] = entity[f"soilcalibration{i}"]
                else: body[f"soilcalibration{i}"] = CalibrationFuction()


            calib = body[f"soilcalibration{i}"]["value"]

            allowed_builtins = {"__builtins__": {"min": min, "max": max}}

            allowed_builtins["x"] = body[f"soilmoistureraw{i}"]["value"]
            for ckey in calib["constants"]:
                allowed_builtins[ckey] = calib["constants"][ckey]

            try:
                v = eval(calib["function"], allowed_builtins, {})
            except:
                v = -1

            body[f"soilmoisturecalibrated{i}"] = SoilMoistureCalibrated(v)

    return body


def calibrate_data_backward(session, entity_id, body):

    # If the body doesn't have the calibration function we need the full entity
    entity = cosmicswamp.get_current_entity_from_id(session, entity_id)

    for i in range(3):

        if (f"soilmoisturecalibrated{i}" in body):

            if f"soilcalibration{i}" in entity: body[f"soilcalibration{i}"] = entity[f"soilcalibration{i}"]
            else: body[f"soilcalibration{i}"] = CalibrationFuction()

            calib = body[f"soilcalibration{i}"]["value"]

            allowed_builtins = {"__builtins__": {"min": min, "max": max}}

            target = body[f"soilmoisturecalibrated{i}"]["value"]

            for ckey in calib["constants"]:
                allowed_builtins[ckey] = calib["constants"][ckey]

            raw_min = 999999
            sm_min = -1

            xvals = []
            yvals = []
            for sm_raw in np.linspace(1,10000,100):
                allowed_builtins["x"] = sm_raw
                yvals.append( eval(calib["function"], allowed_builtins, {}) )
                xvals.append( sm_raw )

            func = scipy.interpolate.interp1d(yvals, xvals) 
            sm_min = func(target)
            
            body[f"soilmoistureraw{i}"] = SoilMoistureRaw(sm_min)

    return body

################################################
# ROUTES CREATE/UP/DELETE
################################################

@router.get("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    time_index: str = None,
                    location: JSONStructure = None,
                    messageindex: int = 0,
                    soiltemperature0: float = 0.0,
                    soiltemperature1: float = 0.0,
                    soiltemperature2: float = 0.0,
                    soilcapacitance0: float = 0,
                    soilcapacitance1: float = 0,
                    soilcapacitance2: float = 0,
                    soilmoistureraw0: float = 0,
                    soilmoistureraw1: float = 0,
                    soilmoistureraw2: float = 0,
                    batteryvoltage: float = 0.0,
                    jsondata: JSONStructure = None
    ):

    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    body = ngsi.compile_entity(jsondata, entity_id, ENTITY_TYPE, time_index, [])

    # Entity header variables
    orion.set_state_source(body, "CREATION", "API")
    ngsi.set_default(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_default(body, "location",      location)

    ngsi.set_default(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_default(body, "messageindex",     MessageIndex(messageindex))
    ngsi.set_default(body, "soiltemperature0", SoilTemperature(soiltemperature0))
    ngsi.set_default(body, "soiltemperature1", SoilTemperature(soiltemperature1))
    ngsi.set_default(body, "soiltemperature2", SoilTemperature(soiltemperature2))
    ngsi.set_default(body, "soilcapacitance0", SoilCapacitance(soilcapacitance0))
    ngsi.set_default(body, "soilcapacitance1", SoilCapacitance(soilcapacitance1))
    ngsi.set_default(body, "soilcapacitance2", SoilCapacitance(soilcapacitance2))
    ngsi.set_default(body, "soilmoistureraw0", SoilMoistureRaw(soilmoistureraw0))
    ngsi.set_default(body, "soilmoistureraw1", SoilMoistureRaw(soilmoistureraw1))
    ngsi.set_default(body, "soilmoistureraw2", SoilMoistureRaw(soilmoistureraw2))
    ngsi.set_default(body, "batteryvoltage",   BatteryVoltage(batteryvoltage))
    ngsi.set_default(body, "soilmoisturecalibrated0", SoilMoistureCalibrated(0.0))
    ngsi.set_default(body, "soilmoisturecalibrated1", SoilMoistureCalibrated(0.0))
    ngsi.set_default(body, "soilmoisturecalibrated2", SoilMoistureCalibrated(0.0))
    ngsi.set_default(body, "soilcalibration0", CalibrationFuction())
    ngsi.set_default(body, "soilcalibration1", CalibrationFuction())
    ngsi.set_default(body, "soilcalibration2", CalibrationFuction())

    cosmicswamp.create_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)

    return body


@router.post("/up/{entity_id}")
def update(request: Request,
                    entity_id,                      
                    time_index: str = None,
                    location: JSONStructure = None,
                    ultralight:  int   = None,
                    messageindex:  int   = None,
                    soiltemperature0:  float = None,
                    soiltemperature1:  float = None,
                    soiltemperature2:  float = None,
                    soilcapacitance0:  float = None,
                    soilcapacitance1:  float = None,
                    soilcapacitance2:  float = None,
                    soilmoistureraw0: float = None,
                    soilmoistureraw1: float = None,
                    soilmoistureraw2: float = None,
                    batteryvoltage:  float = None,
                    jsondata: JSONStructure = None
    ):
    
    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    body = cosmicswamp.compile_entity_state_at_time(request, entity_id, ENTITY_TYPE, time_index, [], jsondata)

    # Entity header variables
    orion.set_state_source(body, "SIMULATED", "API")
    ngsi.set_override(body, "location",      location)
    ngsi.set_override(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_override(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_override(body, "messageindex",     MessageIndex(messageindex))
    ngsi.set_override(body, "ultralight",       UltralightMessage(ultralight))

    ngsi.set_override(body, "soiltemperature0", SoilTemperature(soiltemperature0))
    ngsi.set_override(body, "soiltemperature1", SoilTemperature(soiltemperature1))
    ngsi.set_override(body, "soiltemperature2", SoilTemperature(soiltemperature2))
    ngsi.set_override(body, "soilcapacitance0", SoilCapacitance(soilcapacitance0))
    ngsi.set_override(body, "soilcapacitance1", SoilCapacitance(soilcapacitance1))
    ngsi.set_override(body, "soilcapacitance2", SoilCapacitance(soilcapacitance2))
    ngsi.set_override(body, "soilmoistureraw0", SoilMoistureRaw(soilmoistureraw0))
    ngsi.set_override(body, "soilmoistureraw1", SoilMoistureRaw(soilmoistureraw1))
    ngsi.set_override(body, "soilmoistureraw2", SoilMoistureRaw(soilmoistureraw2))
    ngsi.set_override(body, "soilmoisturecalibrated0", SoilMoistureCalibrated(0.0))
    ngsi.set_override(body, "soilmoisturecalibrated1", SoilMoistureCalibrated(0.0))
    ngsi.set_override(body, "soilmoisturecalibrated2", SoilMoistureCalibrated(0.0))
    ngsi.set_override(body, "batteryvoltage",   BatteryVoltage(batteryvoltage))
    ngsi.set_override(body, "soilcalibration0", CalibrationFuction())
    ngsi.set_override(body, "soilcalibration1", CalibrationFuction())
    ngsi.set_override(body, "soilcalibration2", CalibrationFuction())
        
    # Final commit of new NGSI quantity
    if not cosmicswamp.has_current_entity_from_id(request, entity_id):
        cosmicswamp.create_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
    else:
        cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)
        

@router.post("/iotagent/{entity_id}")
def iotagent(request: Request,
            entity_id,
            time_index: str = None,
            payload_type: str = None,
            payload_data: JSONStructure = None):
    
    # Parsing routines
    # - Thingsboard MQTT TTN Parser based on decoded_payload
    headers = orion.get_fiware_headers(request)
    body = cosmicswamp.build_entity_table(entity_id, ENTITY_TYPE, time_index, None, None)

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
        body = calibrate_data_forward(request, entity_id, body)
        orion.set_state_source(body, "CALIBRATED", "TTN_MQTT")

    print("IoT Message Data", headers, body)
    update(request, entity_id, time_index=time_index, jsondata=body)

    return body

@router.post("/simulate/{entity_id}")
def simulate(request: Request,
                    entity_id,                    
                    time_index: str = None,
                    location: List[float] = None,
                    messageindex: int = None,
                    soiltemperature0:  float = None,
                    soiltemperature1:  float = None,
                    soiltemperature2:  float = None,
                    soilcapacitance0:  float = None,
                    soilcapacitance1:  float = None,
                    soilcapacitance2:  float = None,
                    soilmoistureraw0: float = None,
                    soilmoistureraw1: float = None,
                    soilmoistureraw2: float = None,
                    batteryvoltage:  float = None,
                    jsondata: JSONStructure = None,
                    adc_noise: float = 0.0,
                    adc_offset: float = 0.0
                    ):
    
    # Request standard service path headers
    headers = orion.get_fiware_headers(request)
    time_index = orion.infer_timestamp(time_index)

    # Build the NGSI dictionary from current state
    body = cosmicswamp.compile_entity_state_at_time(request, entity_id, ENTITY_TYPE, time_index, attrs=None, jsondata=None)

    # Entity header variables
    orion.set_state_source(body, "SIMULATED", "API")
    ngsi.set_override(body, "location",      location)
    ngsi.set_override(body, "TimeInstant",   orion.TimeInstant(time_index))
    ngsi.set_override(body, "UploadInstant", orion.TimeInstant(datetime.datetime.now().isoformat()))

    # Device specific variables
    ngsi.set_override(body, "messageindex",            MessageIndex(messageindex))
    ngsi.set_override(body, "soiltemperature0", SoilTemperature(soiltemperature0))
    ngsi.set_override(body, "soiltemperature1", SoilTemperature(soiltemperature1))
    ngsi.set_override(body, "soiltemperature2", SoilTemperature(soiltemperature2))
    ngsi.set_override(body, "soilcapacitance0", SoilCapacitance(soilcapacitance0))
    ngsi.set_override(body, "soilcapacitance1", SoilCapacitance(soilcapacitance1))
    ngsi.set_override(body, "soilcapacitance2", SoilCapacitance(soilcapacitance2))
    ngsi.set_override(body, "soilmoistureraw0", SoilMoistureRaw(soilmoistureraw0))
    ngsi.set_override(body, "soilmoistureraw1", SoilMoistureRaw(soilmoistureraw1))
    ngsi.set_override(body, "soilmoistureraw2", SoilMoistureRaw(soilmoistureraw2))
    ngsi.set_override(body, "soilmoisturecalibrated0", SoilMoistureCalibrated(0.0))
    ngsi.set_override(body, "soilmoisturecalibrated1", SoilMoistureCalibrated(0.0))
    ngsi.set_override(body, "soilmoisturecalibrated2", SoilMoistureCalibrated(0.0))
    ngsi.set_override(body, "batteryvoltage",   BatteryVoltage(batteryvoltage))

    # Calibration Routines
    # - We calibrate backwards every possible value of the three depth gauge
    body = calibrate_data_backward(request, entity_id, body)

    # Smearing Routines
    # - Introduce random smearing to simulated raw data
    for i in range(3):
            
        raw_value = body[f"soilmoistureraw{i}"]["value"]
        raw_shift = np.random.uniform(0.0, adc_noise) + adc_offset

        ngsi.set_override(body, f"soilmoistureraw{i}", raw_value + raw_shift)
        
    # - After smearing we have to calibrate forward again
    body = calibrate_data_forward(request, entity_id, body)

    # Submit to ORION/CRATE
    cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=body)