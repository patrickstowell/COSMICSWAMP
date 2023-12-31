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
from pcse.fileinput import CABOFileReader, YAMLCropDataProvider

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

from .configuration import settings
import modules.iot_platform.cosmicswamp as cosmicswamp
import modules.information_platform.managementzone as managementzone

NULL_VALUE = -999
from typing import Any, Dict, AnyStr, List, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

# Define Usual Router requirement
router = APIRouter(
    prefix="/information-platform/soil",
    tags=["information-platform:soil"],
    dependencies=[Depends(settings), Depends(orion.required_headers)]
)

# Parameter Helpers
def BaseSoil(value): return orion.String(value)
def CarbonContent(value, unit="g/g"): return orion.Number(value, unit)
def LatticeWater(value, unit="g/g"):  return orion.Number(value, unit)
def Porosity(value, unit="m3/m3"):    return orion.Number(value, unit)
def Density(value, unit="g/cm3"):     return orion.Number(value, unit)
def Drainage(value, unit="cm/h"):     return orion.Number(value, unit)
def Campaign(value):                  return orion.String(value)

def WiltingMoisture(value, unit="cm3/cm3"):        return orion.Number(value, unit)
def FieldCapacityMoisture(value, unit="cm3/cm3"):  return orion.Number(value, unit)
def SaturationMoisture(value, unit="cm3/cm3"):     return orion.Number(value, unit)
def AerationSoilAirContent(value, unit="cm3/cm3"): return orion.Number(value, unit)

def HydaulicConductivityMap(value): 
    data = orion.Structured({"data": value})
    data["metadata"]["unit"] = {"type":"String","value":"log (cm/day)"}
    return data


def HydraulicConductivitySaturated(value, unit="cm/day"): return orion.Number(value, unit)
def PercolationRateRootZone(value, unit="cm/day"): return orion.Number(value, unit)
def PercolationRateSubSoil(value, unit="cm/day"):  return orion.Number(value, unit)
def PercolationRateSubSoil(value, unit="cm/day"):  return orion.Number(value, unit)

def SeepageTopsoilDeepPar1(value): return orion.Number(value)
def SeepageTopsoilDeepPar2(value): return orion.Number(value)
def SeepageTopsoilShallowPar1(value): return orion.Number(value)
def SeepageTopsoilShallowPar2(value): return orion.Number(value)
def MoistureDeficitySeedbed(value):   return orion.Number(value)
def SoilDepth(value, unit="cm"):   return orion.Number(value, unit)
def SoilType(value):   return orion.String(value)

pcse_mapping = {
    "SMW":     ["wiltingMoisture", WiltingMoisture, "soil moisture content at wilting point [cm3/cm3]"],
    "SMFCF":   ["fieldCapacityMoisture", FieldCapacityMoisture,  "soil moisture content at field capacity [cm3/cm3]"],
    "SM0":     ["saturationMoisture", SaturationMoisture, "soil moisture content at saturation [cm3/cm3]"],
    "CRAIRC":  ["aerationSoilAirContent", AerationSoilAirContent, "critical soil air content for aeration [cm3/cm3]"],
    # "CONTAB":  ["hydaulicConductivityMap", HydaulicConductivityMap,"10-log hydraulic conductivity as function of pF [log (cm); log (cm/day)"],
    "K0":      ["hydraulicConductivitySaturated", HydraulicConductivitySaturated, "hydraulic conductivity of saturated soil [cm day-1]"],
    "SOPE":    ["percolationRateRootZone", PercolationRateRootZone, "maximum percolation rate root zone[cm day-1]"],
    "KSUB":    ["percolationRateSubSoil", PercolationRateSubSoil, "maximum percolation rate subsoil [cm day-1]"],
    "SPADS":   ["seepageTopsoilDeepPar1", SeepageTopsoilDeepPar1, "1st topsoil seepage parameter deep seedbed"],
    "SPODS":   ["seepageTopsoilDeepPar2", SeepageTopsoilDeepPar2, ""],
    "SPASS":   ["seepageTopsoilShallowPar1", SeepageTopsoilShallowPar1, ""],
    "SPOSS":   ["seepageTopsoilShallowPar2", SeepageTopsoilShallowPar2, ""],
    "DEFLIM":  ["moistureDeficitySeedbed", MoistureDeficitySeedbed, ""],
    "RDMSOL":  ["soilDepth", SoilDepth, ""],
    "SOLNAM":  ["soilType", SoilType, ""],
    "DRAIN":   ["drainage", Drainage, ""],
    "LATWAT":  ["latticeWater", LatticeWater, ""],
    "CARB":    ["carbonContent", CarbonContent, ""]
}

@router.get("/create/soil/{entity_id}")
def create(request: Request,
                    entity_id,
                    attrs: List[str] = None,
                    time_index: str = None,
                    jsondata: JSONStructure = None,
                    location: dict = geojson.point(),
                    base: str = "ec3.soil",
                    density: float = 1.2, # g/g
                    carboncontent: float = 0.3,
                    latticewater: float = 0.1,
                    drainage: float = 0.1,
                    wiltingMoisture: float = None,
                    fieldCapacityMoisture: float = None,
                    saturationMoisture: float = None, 
                    aerationSoilAirContent: float = None,
                    hydaulicConductivityMap: list = None,
                    hydraulicConductivitySaturated: float = None,
                    percolationRateRootZone: float = None,
                    percolationRateSubSoil: float = None,
                    seepageTopsoilDeepPar1: float = None,
                    seepageTopsoilDeepPar2: float = None,
                    seepageTopsoilShallowPar1: float = None,
                    seepageTopsoilShallowPar2: float = None,
                    moistureDeficitySeedbed: float = None,
                    soilDepth: float = None,
                    soilType: float = None,
                    campaign: str = None
    ):

    headers = orion.get_fiware_headers(request)

    entity_type = "Soil"

    body = cosmicswamp.build_entity_table(entity_id, "Soil", attrs, time_index, jsondata)

    soil_template = CABOFileReader(f"./WOFOST_soil_parameters/{base}")
    
    for key in pcse_mapping: 
        if key in soil_template:
            print("SOIL", key, soil_template[key])
            func = pcse_mapping[key][1]
            ngsi.set_default(body, pcse_mapping[key][0], func(soil_template[key]))

    orion.set_state_source(body, "CREATION", "API")
    ngsi.set_default(body, "location", location)

    ngsi.set_default(body, "baseSoil", BaseSoil(base))

    ngsi.set_default(body, "density", Density(density))
    ngsi.set_default(body, "carboncontent", CarbonContent(carboncontent))
    ngsi.set_default(body, "latticewater", LatticeWater(latticewater))
    ngsi.set_default(body, "drainage", Drainage(drainage))
    ngsi.set_default(body, "campaign", Campaign(campaign))
    ngsi.set_default(body, "wiltingMoisture", WiltingMoisture(wiltingMoisture))
    ngsi.set_default(body, "fieldCapacityMoisture", FieldCapacityMoisture(fieldCapacityMoisture))
    ngsi.set_default(body, "saturationMoisture", SaturationMoisture(saturationMoisture))
    ngsi.set_default(body, "aerationSoilAirContent", AerationSoilAirContent(aerationSoilAirContent))
    ngsi.set_default(body, "hydaulicConductivityMap", HydaulicConductivityMap(hydaulicConductivityMap))
    ngsi.set_default(body, "hydraulicConductivitySaturated", HydraulicConductivitySaturated(hydraulicConductivitySaturated))
    ngsi.set_default(body, "hydraulicConductivitySaturated", HydraulicConductivitySaturated(hydraulicConductivitySaturated))
    ngsi.set_default(body, "percolationRateRootZone", PercolationRateRootZone(percolationRateRootZone))
    ngsi.set_default(body, "percolationRateSubSoil", PercolationRateSubSoil(percolationRateSubSoil))
    ngsi.set_default(body, "seepageTopsoilDeepPar1", SeepageTopsoilDeepPar1(seepageTopsoilDeepPar1))
    ngsi.set_default(body, "seepageTopsoilDeepPar2", SeepageTopsoilDeepPar2(seepageTopsoilDeepPar2))
    ngsi.set_default(body, "seepageTopsoilShallowPar1", SeepageTopsoilShallowPar1(seepageTopsoilShallowPar1))
    ngsi.set_default(body, "seepageTopsoilShallowPar2", SeepageTopsoilShallowPar2(seepageTopsoilShallowPar2))
    ngsi.set_default(body, "moistureDeficitySeedbed", MoistureDeficitySeedbed(moistureDeficitySeedbed))
    ngsi.set_default(body, "soilDepth", SoilDepth(soilDepth))
    ngsi.set_default(body, "soilType", SoilType(soilType))

    print(body["soilDepth"])
    cosmicswamp.create_entity(request, entity_id, jsondata=body)
    cosmicswamp.update_entity(request, entity_id, entity_type, jsondata=body)

    return body

def pcse_soil_from_ngsi(insoil):

    base = insoil["baseSoil"]["value"]
    soil_template = CABOFileReader(f"./WOFOST_soil_parameters/{base}")

    for key in pcse_mapping:
        convkey = pcse_mapping[key][0]
        if convkey in insoil:
            soil_template[key] = insoil[convkey]["value"]
        
    return soil_template