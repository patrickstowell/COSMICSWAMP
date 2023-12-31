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

import dependencies.orion_utils as orion
import dependencies.crate_utils as crate
import dependencies.ngsi_utils as ngsi
import dependencies.geojson_utils as geojson

from .configuration import settings
import modules.iot_platform.cosmicswamp as cosmicswamp

NULL_VALUE = -999
from typing import Any, Dict, AnyStr, List, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

# Define Usual Router requirement
router = APIRouter(
    prefix="/information-platform/managementzone",
    tags=["information-platform:managementzone"],
    dependencies=[Depends(settings), Depends(orion.required_headers)]
)

@router.post("/create/{entity_id}")
def create(request: Request,
                    entity_id,
                    attrs: List[str] = None,
                    time_index: str = None,
                    jsondata: JSONStructure = None,
                    location: dict = None,
                    zoneid: str = None,
                    commit: bool = True
    ):

    field_body = cosmicswamp.build_entity_table(entity_id, "ManagementZone", attrs, time_index, jsondata)
    
    if location: field_body["location"] = location

    ngsi.set_default(field_body, "zoneid", orion.String(zoneid))

    if commit:
        cosmicswamp.create_entity(request, entity_id, jsondata=field_body)
        cosmicswamp.update_entity(request, entity_id, jsondata=field_body)

    return field_body

@router.post("/update/{entity_id}")
def update(request: Request,
                    entity_id,
                    attrs: List[str] = None,
                    time_index: str = None,
                    jsondata: JSONStructure = None,
                    location: dict = None,
                    zoneid: str = None,
                    commit: bool = True
    ):

    field_body = cosmicswamp.build_entity_table(entity_id, "ManagementZone", attrs, time_index, jsondata)
    
    if location: field_body["location"] = location

    ngsi.set_default(field_body, "zoneid", orion.String(zoneid))

    field_body["type"] = "ManagementZone"

    cosmicswamp.update_entity(request, entity_id, entity_type="ManagementZone", jsondata=field_body)

    return field_body

@router.post("/delete/{entity_id}")
def delete(request: Request,
            entity_id,
            purge: bool = False
    ):
    cosmicswamp.delete_entity(request, entity_id, purge)

@router.post("/all_at_location")
def all_at_location(request: Request,
            entity_id,
            coords: Annotated[str | None, Query(description="Co-ordinates lat/lon")] = None
    ):
    return cosmicswamp.get_entities_by_type_and_geometry(request, "ManagementZone", coords)

