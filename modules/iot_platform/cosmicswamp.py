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
import dependencies.log_utils as log

NULL_VALUE = -999

from typing import Any, Dict, AnyStr, List, Union

JSONStructure = Union[Dict[str, Any], List[Any]]

# Define Usual Router requirement
router = APIRouter(
    prefix="/iot-platform/cosmicswamp",
    tags=["cosmicswamp","iot-platform"],
    dependencies=[Depends(settings), Depends(orion.required_headers)]
)
router.verbosity = log.DEBUG

@router.get("/")
def root():
    return "COSMICSWAMP-API"


@router.get("/status")
def status():
    return {"status": "OK"}


# -----------------------------
# SESSION CREATION
# -----------------------------
def get_new_session(service, servicepath):
    session = orion.session(service, servicepath)
    return session

def get_session_from_dict(store):
    return get_new_session(store["Fiware-Service"], store["Fiware-Servicepath"])

def create_root_session_map():

    log.debug(router, "Creating ROOT Session map.")

    root_session = orion.session(servicepath="/root")
    root_headers = orion.get_fiware_headers(root_session)

    root_body = {
            "id": "urn:ngsi-ld:SessionMap",
            "type": "SessionMap",
            "sessions": {"type": "StructuredValue", "value": {}}
        }
    
    try:
        url = settings().orion_url + f"/v2/entities"
        r = orion.post(url, root_headers, json=root_body)
    except:
        url = settings().orion_url + f"/v2/entities/urn:ngsi-ld:SessionMap/attrs"
        del root_body["id"]
        del root_body["type"]
        r = orion.post(url, root_headers, json=root_body)


@router.get("/has/session")
def has_session(request: Request):

    headers   = orion.get_fiware_headers(request)

    root_session = orion.session(servicepath="/root")
    root_headers = orion.get_fiware_headers(root_session)

    url = settings().orion_url + f"/v2/entities/urn:ngsi-ld:SessionMap"
    r = orion.get(url, root_headers)

    if not r: 
        create_root_session_map()
        return False
        
    return headers["Fiware-Service"]+headers["Fiware-Servicepath"] in r["sessions"]["value"]


@router.get("/session")
def get_session():

    root_session = orion.session(servicepath="/root")
    headers   = orion.get_fiware_headers(root_session)

    url = settings().orion_url + f"/v2/entities/urn:ngsi-ld:SessionMap"
    r = orion.get(url, headers)
    return r



@router.post("/session")
def register_session(request: Request):

    headers   = orion.get_fiware_headers(request)

    root_session = orion.session(servicepath="/root")
    root_headers = orion.get_fiware_headers(root_session)

    url = settings().orion_url + f"/v2/entities/urn:ngsi-ld:SessionMap"
    r = orion.get(url, root_headers)

    if not r: 
        create_root_session_map()
        return False
    
    r["sessions"]["value"][headers["Fiware-Service"]+headers["Fiware-Servicepath"]] = True

    url = settings().orion_url + f"/v2/entities/urn:ngsi-ld:SessionMap/attrs"
    del r["id"]
    del r["type"]
    r = orion.post(url, root_headers, json=r)

    return


@router.delete("/session")
def delete_session(request: Request, 
purge: bool = False):

    headers   = orion.get_fiware_headers(request)
    log.debug(router, "DELETING ENTY", headers)

    entities = get_all_current_entity_ids(request)
    log.debug(router, "DELETING ENTY", entities, headers)

    for e in entities:
        log.debug(router, "Deleting entity", e)
        delete_entity(request, e["id"], e["type"], purge=purge)
        log.debug(router, "Failed")

    root_session = orion.session(servicepath="/root")
    root_headers = orion.get_fiware_headers(root_session)
    root_exists = True

    root_body = get_current_entity_from_id(root_session, "urn:ngsi-ld:SessionMap")
    
    del root_body["sessions"]["value"][headers["Fiware-Service"]+headers["Fiware-Servicepath"]]

    url = settings().orion_url + f"/v2/entities/urn:ngsi-ld:SessionMap/attrs"
    del root_body["id"]
    del root_body["type"]

    orion.post(url, root_headers, json=root_body)
    
    # Now purge all from the path
    for e in get_all_current_entity_ids(request):
        try:
            delete_entity(request, e["id"], purge=True)
        except:
            pass

# -----------------------------
# MANAGEMENT
# -----------------------------

@router.get("/mapping/{entity_id}")
def map_entity(request: Request, entity_id):
    log.debug(router, request, entity_id)

@router.post("/entity/{entity_id}")
def update_entity(request: Request, 
        entity_id: str,
        entity_type: str = None,
        time_index: str = None,
        attrs: List[str] = None,
        jsondata: JSONStructure = None
    ):
    
    headers = orion.get_fiware_headers(request)

    entity_id = ngsi.format_id(entity_id)

    body = jsondata

    body = ngsi.dict_keys_to_str(body)
    body = ngsi.check_format(body, entity_id)
    body = ngsi.update_from_attr(body, attrs)
    body = ngsi.update_time_index(body, time_index)
    body = ngsi.coerce_data(body)

    if "id" in body: del body["id"]
    if "type" in body: del body["type"]
    url = settings().orion_url + f"/v2/entities/{entity_id}/attrs"
    # log.debug(router, "##################")
    # log.debug(router, "Posting orion UPDATE FIRST", body)
    r = orion.post(url, headers, body)

    # Now notify quantum leap
    # log.debug(router, "QUANTUM LEAP ", json.loads(json.dumps(body)))
    url = "http://backend-quantumleap:8668/v2/notify"
    body["id"] = entity_id
    body["type"] = entity_type
    # ngsi.pretty_log.debug(router, body)
    # print(body)

    # if "location" in body:
        # body["location"]["type"] = "GEO_SHAPE"
    body = {
        "data": [body],
        "subscriptionId": "654db53240157754c3d09cdf"
    }
    r = orion.post(url, headers, body)
    # log.debug(router, "##################")
    # log.debug(router, "Updated QuantumLeap", body)
    # log.debug(router, "##################")

    # else:
    #     log.debug(router, "Creating new")
    #     url = settings().orion_url + f"/v2/entities/{entity_id}"
    #     r = orion.post(url, headers, body)

    return "200"


@router.post("/entity/{entity_id}")
def create_entity(request: Request, 
        entity_id: str,
        entity_type: str = None,
        attrs: List[str] = None,
        time_index: str = None,
        jsondata: JSONStructure = None
    ):
    
    # if not has_session(request): create_session(request)

    headers = orion.get_fiware_headers(request)

    entity_id = ngsi.format_id(entity_id)

    body = jsondata

    body = ngsi.dict_keys_to_str(body)
    body = ngsi.check_format(body, entity_id)
    body = ngsi.update_from_attr(body, attrs)
    body = ngsi.update_time_index(body, time_index)
    body = ngsi.coerce_data(body)
    body = ngsi.check(body)

    body["id"] = entity_id

    url = settings().orion_url + f"/v2/entities"
            
    if not has_current_entity_from_id(request, entity_id):
        r = orion.post(url, headers, json=body)
    else:
        url += f"/{entity_id}/attrs" 
        del body["id"]
        del body["type"]
        r = orion.post(url, headers, json=body)

    
    return r


@router.post("/construct/{entity_id}")
def build_entity_table(
        entity_id: str,
        entity_type: str = None,
        attrs: List[str] = None,
        time_index: str = None,
        jsondata: JSONStructure = None
    ):

    entity_id = ngsi.format_id(entity_id)

    body = jsondata

    body = ngsi.dict_keys_to_str(body)
    body = ngsi.check_format(body, entity_id)
    body = ngsi.update_from_attr(body, attrs)
    body = ngsi.update_time_index(body, time_index)
    body = ngsi.coerce_data(body)

    if entity_type != None:
        body["type"] = entity_type


    return body


@router.post("/delete/entity/{entity_id}")
def delete_entity(request: Request, 
        entity_id: str,
        entity_type: str = None,
        purge: bool = False
    ):
    
    headers = orion.get_fiware_headers(request)

    entity_id_orig = entity_id
    entity_id = ngsi.format_id(entity_id)
    url = settings().orion_url + f"/v2/entities/{entity_id}"

    deleted = True
    try: orion.delete(url, headers)
    except: deleted = False

    if entity_type and not deleted:
        deleted = True
        url += f"?type={entity_type}"
        try: orion.delete(url, headers)
        except: deleted = False
        
    if not deleted:
        deleted = True
        url = settings().orion_url + f"/v2/entities/{entity_id_orig}"
        try:  
            r = orion.delete(url, headers)
            # log.debug(router, r)
        except: deleted = False

        deleted = True
        url = settings().orion_url + f"/v2/entities/{entity_id_orig}?type={entity_type}"
        try:  
            r = orion.delete(url, headers)
            # log.debug(router, r)
        except: deleted = False

    if purge:    
        try:
            delete_timeseries_for_entity(request, entity_id, entity_type )
        except:
            pass

    return "200"


@router.post("/delete/entity/{entity_id}")
def purge_entity(request: Request, 
        entity_id: str,
    ):
    
    headers = orion.get_fiware_headers(request)

    entity_id = ngsi.format_id(entity_id)
    url = settings().orion_url + f"/v2/entities/{entity_id}"

    delete_entity(request, entity_id)
    # delete_historic_data_for_entity(entity_id)

    return "200"


# -----------------------------
# CURRENT STATES
# -----------------------------
@router.get("/current/entity")
def get_all_current_entity_ids(request: Request, 
        limit: Annotated[int | None, Query(description="Max entities")] = 100
    ):
    headers = orion.get_fiware_headers(request)
    url = settings().orion_url + f"/v2/entities?attrs=id,type&limit={limit}"
    log.debug(router, url, headers)
    r = orion.get(url, headers)
    return r


@router.get("/has/entity/{entity_id}")
def has_current_entity_from_id(request: Request, 
        entity_id: str
    ):
    entity_id = ngsi.format_id(entity_id)
    headers = orion.get_fiware_headers(request)
    try:
        url = settings().orion_url + f"/v2/entities/{entity_id}"
        entity = orion.get(url, headers, silentfail=True)
        # log.debug(router, entity, url )
        return "id" in entity
    except:
        return False

@router.get("/current/entity/{entity_id}")
def get_current_entity_from_id(request: Request, 
        entity_id: str
    ):

    entity_id = ngsi.format_id(entity_id)
    headers = orion.get_fiware_headers(request)
    try:
        url = settings().orion_url + f"/v2/entities/{entity_id}"
        r = orion.get(url, headers)
        return r
    except:
        return {}


@router.get("/current/type")
def get_all_current_entity_types(request: Request, 
        limit: Annotated[int | None, Query(description="Max entities")] = 100
    ):
    
    headers = orion.get_fiware_headers(request)
    url = settings().orion_url + f"/v2/types?limit={limit}"
    r = orion.get(url, headers)
    return r


@router.get("/current/type/{entity_type}")
def get_all_current_entities_of_type(request: Request, 
        entity_type: str,
        limit: int = 1000
    ):

    headers = orion.get_fiware_headers(request)
    url = settings().orion_url + f"/v2/entities?type={entity_type}&limit={limit}"
    r = orion.get(url, headers)

    return r


@router.get("/current/geo/{entity_type}")
def get_entities_by_type_and_geometry(request: Request,
        entity_type: str,
        coords: Annotated[str | None, Query(description="Co-ordinates lat/lon")] = None,
        maxDistance: Annotated[int | None, Query(description="Max distance in m")] = 1000,
        crs: Annotated[str | None, Query(description="Co-ordinate system.")] = "WGS84",
        location: dict = None
    ):

    url = orion.build_geo_query(entity_type, coords, crs, maxDistance)
    headers = orion.get_fiware_headers(request)
    # url = settings().orion_url + f"/v2/entities?type={entity_type}"
    r = orion.get(url, headers)

    return r


# -----------------------------
# HISTORIC_DATA
# -----------------------------

@router.get("/historic/entity/{entity_id}")
def get_series_data_for_entity(request: Request,
                    entity_id,
                    attrs: List[str] = None,
                    limit: int = 1000,
                    orderBy: str = "time_index",
                    groupBy: str = None,
                    cuts: List[str] = None,
                    ascending: bool = True
    ):

    #print("GETTING SERIES DATA")

    # Get the orion entity from ORION to determine type.    
    entity_id = ngsi.format_id(entity_id)
    headers = orion.get_fiware_headers(request)
    
    
    entity = get_current_entity_from_id(request, entity_id)
    if not entity: return []
    entity_type = entity["type"].lower()

    # Build request as usual
    headers = orion.get_fiware_headers(request)

    sql = "SELECT"
    sql += ' ' + crate.query_attrs(attrs)
    sql += ' ' + crate.query_table_from_headers_and_type(headers, entity_type) 
    sql += ' ' + crate.query_entity(entity_id)
    sql += ' ' + crate.query_cut_filter(cuts)
    sql += ' ' + crate.query_groupby_filter(groupBy)
    sql += ' ' + crate.query_orderby_filter(orderBy, ascending)
    sql += ' ' + crate.query_limit_filter(limit)

    log.debug(router, "SELECTION", sql)
    #print("SETTINGS", settings().crate_pd)
    data = crate.query_retrieve_pandas(sql, settings().crate_pd)

    return data
    

@router.get("/historic/type/{type}")
def get_series_data_for_all_entities_of_type(request: Request,
                    entity_type,
                    attrs: List[str] = None,
                    limit: int = 1000,
                    orderBy: str = "time_index",
                    groupBy: str = None,
                    cuts: List[str] = None,
                    ascending: bool = True
    ):

    # Get the orion entity from ORION to determine type.    
    entity_type = entity_type.lower()

    # Build request as usual
    headers = orion.get_fiware_headers(request)

    sql = "SELECT"
    sql += ' ' + crate.query_attrs(attrs)
    sql += ' ' + crate.query_table_from_headers_and_type(headers, entity_type) 
    sql += ' ' + crate.query_cut_filter(cuts)
    sql += ' ' + crate.query_groupby_filter(groupBy)
    sql += ' ' + crate.query_orderby_filter(orderBy, ascending)
    sql += ' ' + crate.query_limit_filter(limit)

    data = crate.query_retrieve_pandas(sql, settings().crate_pd)

    return data


# def create_entity_from_body(entity_id, headers, body):

#     entity_id = ngsi.format_id(entity_id)
#     body["id"] = entity_id
#     try:
#         url = settings().orion_url + f"/v2/entities"
#         r = orion.post(url, headers, body)
#     except:
#         log.debug(router, "Device exists", url)


def create_subscription_from_body(entity_id, headers, body):
    return "SUBSCRIPTION CREATED"

def delete_subscription_for_entity(request, entity_id):
    return "DELETED SUBSCRIPTION"

def delete_timeseries_for_entity(request, entity_id, entity_type):

    # Get the orion entity from ORION to determine type.    
    entity_id = ngsi.format_id(entity_id)
    
    entity_type = entity_type.lower()

    # Build request as usual
    headers = orion.get_fiware_headers(request)

    attrs = ["entity_id"]
    attrs.append("*")
    
    sql = "DELETE"
    sql += ' ' + crate.query_table_from_headers_and_type(headers, entity_type) 
    sql += ' ' + crate.query_entity(entity_id)
    # sql += ' ' + crate.query_limit_filter(1)

    # log.debug(router, "MY DELETE SQL QUERY ", sql)

    data = crate.query_retrieve_pandas(sql, settings().crate_pd)
    return 


def compile_entity_state_at_time(request, entity_id, entity_type, time_index, attrs, jsondata, nearest=True, inference=False):
    body = ngsi.compile_entity(jsondata, entity_id, entity_type, time_index, attrs)
    if inference and has_current_entity_from_id(request, entity_id):
        body = estimate_entity_state_at_time(request, entity_id, time_index)
    return body

def estimate_entity_state_at_time(request, entity_id, time_index, nearest=True):
    
    # Get the orion entity from ORION to determine type.    
    entity_id = ngsi.format_id(entity_id)
    
    entity = get_current_entity_from_id(request, entity_id)
    entity_type = entity["type"].lower()

    # Build request as usual
    headers = orion.get_fiware_headers(request)

    TS = pd.to_datetime(orion.infer_timestamp(time_index)).timestamp()*1000.0

    TS_DISTANCE = f"(time_index - {TS})"
    if nearest: TS_DISTANCE = "ABS" + TS_DISTANCE

    attrs = ["entity_id"]
    # for key in entity: 
    #     if "id" in key: continue
    #     if "type" in key: continue
    #     attrs.append(key.lower())
    attrs.append("*")
    
    attrs.append(TS_DISTANCE + " AS DIF")
    attrs.append("time_index as TimeInstant")
    attrs.append("time_index as UploadInstant")

    sql = "SELECT"
    sql += ' ' + crate.query_attrs(attrs)
    sql += ' ' + crate.query_table_from_headers_and_type(headers, entity_type) 
    sql += ' ' + crate.query_entity(entity_id)
    sql += ' ' + crate.query_orderby_filter(TS_DISTANCE, ascending=True)
    sql += ' ' + crate.query_limit_filter(1)

    # log.debug(router, "MY SQL QUERY ", sql)

    data = crate.query_retrieve_pandas(sql, settings().crate_pd)
    if len(data) == 0: return entity
        
    for key in entity: 
        if "id" in key: continue
        if "type" in key: continue
        if key.lower() not in data[0]: 
            continue
        entity[key]["value"] = data[0][key.lower()]

    return entity


# @router.get("/queryexternal")
# def query_external_as_json(request: Request,
#                 url: str = None,
#                 backup_url: str = None,
#                 body: str = None
#     ):



def create_test():
    ts = "1" 
    session = get_new_session(f"unittest{ts}",f"/unittest{ts}")
    register_session(session)
    return session

def delete_test(session):
    return delete_session(session)