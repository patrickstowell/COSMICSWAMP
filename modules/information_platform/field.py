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

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson

import modules.iot_platform.cosmicswamp as cosmicswamp

import modules.information_platform.configuration as configuration
import modules.information_platform.managementzone as managementzone


###################################################
# ENTITY MODEL : Field
###################################################
ENTITY_TYPE = "Field"
ENTITY_TYPE_lower = ENTITY_TYPE.lower()


###################################################
# COMMON ROUTER 
###################################################
router = APIRouter(
    prefix="/information-platform/field",
    tags=["information-platform:field"],
    dependencies=[Depends(configuration.settings), Depends(orion.required_headers)]
)


###################################################
# DATA MODEL
###################################################
def data_model(request: Request,
        entity_id: str,
        attrs: list = None,
        time_index: float = None,
        jsondata: dict = None,
        label: str = None,
        center_location: dict = None, 
        radius: float = None,
        location: dict = None,
        farm_relation: str = None
        ):

    field_body = cosmicswamp.build_entity_table(entity_id, 
                                                ENTITY_TYPE, 
                                                attrs, 
                                                time_index, 
                                                jsondata)
    
    if radius and center_location:
        field_body["location"] = geojson.circle_around_point(geojson.point(center_location), 
                                                            radius, 
                                                            nsegments=24)

    if location:
        field_body["location"] = {}
        field_body["location"]["value"] = location

    return field_body


###################################################
# STANDARD CREATE/UP/DELETE
###################################################
@router.post("/create/{entity_id}")
def create(request: Request,
        entity_id: str,
        attrs: list = None,
        time_index: float = None,
        jsondata: dict = None,
        label: str = None,
        center_location: dict = None, 
        radius: float = None,
        location: dict = None,
        farm_relation: str = None,
        commit: bool = True
    ):

    field_body = data_model(request, 
        entity_id,
        attrs,
        time_index,
        jsondata,
        label,
        center_location,
        radius,
        location,
        farm_relation)

    if commit:
        cosmicswamp.create_entity(request, entity_id, ENTITY_TYPE, jsondata=field_body)

    return field_body


@router.post("/up/{entity_id}")
def up(request: Request,
        entity_id: str,
        attrs: list = None,
        time_index: float = None,
        jsondata: dict = None,
        label: str = None,
        center_location: dict = None, 
        radius: float = None,
        location: dict = None,
        farm_relation: str = None,
    ):

    field_body = data_model(request, 
        entity_id,
        attrs,
        time_index,
        jsondata,
        label,
        center_location,
        radius,
        location,
        farm_relation)

    cosmicswamp.update_entity(request, entity_id, ENTITY_TYPE, jsondata=field_body)

    return field_body


@router.post("/delete/{entity_id}")
def delete(request: Request,
            entity_id,
            purge: bool = False
    ):
    cosmicswamp.delete_entity(request, entity_id, purge)

###################################################
# ENTITY SPECIFIC TOOLS
###################################################
@router.post("/split_into_radial_zones/{entity_id}")
def split_into_radial_zones(request: Request,
            entity_id,
            naround : int = 6,
            nradial : int = 3,
            maxdistance: float = None
    ):

    field_body = cosmicswamp.get_current_entity_from_id(request, entity_id)
    
    if field_body["location"]["value"]["type"] != "Polygon":
        print("Field can't be split if its not a Polygon.")
        return []
    
    coords = field_body["location"]["value"]["coordinates"]

    latvals = []
    lonvals = []

    for vals in coords[0]:
        latvals.append(vals[1])
        lonvals.append(vals[0])

    del latvals[0]
    del lonvals[0]

    maxdistance_fromlat = geojson.latlon_distance(min(latvals),statistics.mean(lonvals),max(latvals), statistics.mean(lonvals))/2
    maxdistance_fromlon = geojson.latlon_distance(min(latvals),statistics.mean(lonvals),max(latvals), statistics.mean(lonvals))/2

    field_center = [statistics.mean(lonvals), statistics.mean(latvals)]

    maxdistance_main = (maxdistance_fromlat+maxdistance_fromlon)/2

    zone_id_list = []

    twopi = 3.141519*2
    for i in range(naround):
        for j in range(nradial):

            thetastep1  = -i*(twopi/float(naround))
            thetastep2  = -(i+1)*(twopi/float(naround))

            radialstep1 = j*(maxdistance_main/float(nradial))
            radialstep2 = (j+1)*(maxdistance_main/float(nradial))


            zone_entity_id = entity_id + f":ManagementZone:{i}-{j}"

            segments = []
            segments.append(geojson.latlon_bearing_shift(field_center[1], field_center[0], thetastep1, radialstep1))
            segments.append(geojson.latlon_bearing_shift(field_center[1], field_center[0], thetastep1, radialstep2))
            segments.append(geojson.latlon_bearing_shift(field_center[1], field_center[0], thetastep2, radialstep2))
            segments.append(geojson.latlon_bearing_shift(field_center[1], field_center[0], thetastep2, radialstep1))
            segments.append(geojson.latlon_bearing_shift(field_center[1], field_center[0], thetastep1, radialstep1))

            segmentsswapped = []
            for val in segments:
                segmentsswapped.append([val[1],val[0]])
            poly = geojson.polygon(segmentsswapped)

            template = managementzone.create(request, zone_entity_id, commit=False)

            template["location"] = {}
            template["location"]["type"] = "geo:json"
            template["location"]["value"] = geojson.coerce(poly)

            template["zoneid"] = orion.String(f"{i}-{j}")
            
            cosmicswamp.create_entity(request, zone_entity_id, jsondata=template)
            zone_id_list.append(zone_entity_id)


    field_body["zones"] = orion.Structured({"id":zone_id_list})
    cosmicswamp.update_entity(request, entity_id, "Field", jsondata=field_body)


def get_associated_zones(request: Request, entity_id):

    entity = cosmicswamp.get_current_entity_from_id(request, entity_id)
    if "zones" not in entity: return []

    zone_list = []
    for zone in entity["zones"]["value"]["id"]:
        zone_list.append(cosmicswamp.get_current_entity_from_id(request, zone))

    return zone_list



