from fastapi import FastAPI, HTTPException
from typing import Union

from fastapi import FastAPI, Request
from fastapi import FastAPI, Header
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from typing import Annotated
from fastapi import FastAPI, Query
from fastapi.encoders import jsonable_encoder
import datetime
from colorama import  Back, Style, Fore


import os
import requests
import json
import logging
import datetime
import pandas as pd
from typing import List
import time
from dependencies import geojson_utils


NULL_VALUE = -999
from typing import Any, Dict, AnyStr, List, Union
JSONStructure = Union[Dict[str, Any], List[Any]]

def String(value : str, units=None):
    if value == None: return None
    value = str(value)
    v = {"type": "Text", "value": value, "metadata": {} }
    return v

def Structured(value):
    if value == None: return None
    v = {"type": "StructuredValue", "value": dict(value), "metadata": {} }
    return v

def Number(value : float, units=None):
    if value == None: return None
    value = float(value)
    v = {"type": "Number", "value": value, "metadata": {} }
    if units: v["metadata"]["units"] = {"type": "String", "value": units}
    return v

def Int(value : int, units=None):
    if value == None: return None
    value = int(value)
    v = {"type": "Number", "value": value, "metadata": {} }
    if units: v["metadata"]["units"] = {"type": "String", "value": units}
    return v

def TimeInstant(value=None):
    if value == None: return None
    timestamp = value
    if timestamp == None: timestamp = datetime.datetime.now().isoformat()
    if isinstance(timestamp, str): timestamp = pd.to_datetime(timestamp).isoformat()
    if isinstance(timestamp, datetime.datetime): timestamp = timestamp.isoformat()

    return {"type": "DateTime", "value": timestamp}

def GeoJSON(value):
    if value == None: return None
    v = {"type": "geo:json", "value": value, "metadata": {} }
    return v

def EntityState(value): 
    return String(value)

def EntitySource(value): 
    return String(value)

# -----------------------------
# ORION Functions
# -----------------------------
def get(url, headers, silentfail=False):

    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        if silentfail: return {}
        # print(url, headers, r.text)
        raise HTTPException(status_code=r.status_code,
                            detail="Failed to get valid ORION data : " +
                                    f"{r.status_code} {r.text}")

    return r.json()


def post(url, headers, json):

    headers["Content-Type"] = "application/json"
    #print(url, headers, json)
    r = requests.post(url, headers=headers, json=json, timeout=10)
    if r.status_code > 400:
        # print(url, r.text, headers, json)
        print(Fore.BLACK + "---------")
        print(Fore.RED + "- ERROR -")
        print(Fore.RED + " -> URL  : ", url)
        print(Fore.RED + " -> HEAD : ", headers)
        print(Fore.RED + " -> STAT : ", r.status_code)
        print(Fore.RED + " -> TEXT : ", r.text)
        print(Fore.BLACK + "---------")

        raise HTTPException(status_code=r.status_code,
                            detail="Failed to get valid ORION data : " +
                                    f"{r.status_code} {r.text}")

    return r.text

def patch(url, headers, json):

    headers["Content-Type"] = "application/json"
    r = requests.patch(url, headers=headers, json=json)
    if r.status_code > 400:
        # print(url, r.text, headers, json)
        raise HTTPException(status_code=r.status_code,
                            detail="Failed to get valid ORION data : " +
                                    f"{r.status_code}")

    return r.text


def delete(url, headers):

    r = requests.delete(url, headers=headers)
    if r.status_code > 400:
        print(Fore.BLACK + "---------")
        print(Fore.RED + "- ERROR -")
        print(Fore.RED + " -> URL  : ", url)
        print(Fore.RED + " -> HEAD : ", headers)
        print(Fore.RED + " -> STAT : ", r.status_code)
        print(Fore.RED + " -> TEXT : ", r.text)
        print(Fore.BLACK + "---------")

        
        raise HTTPException(status_code=r.status_code,
                            detail="Failed to delete valid ORION data : " +
                                    f"{r.status_code}")

    return r.text

def build_geo_query(entity_type, coords, crs, maxDistance):

    coords_values = (coords.split(";"))
    # del coords_values[0]
    coords_values.reverse()    
    for i in range(len(coords_values)):
        coords_values[i] = coords_values[i].split(",")

    if len(coords_values) == 1:
        georel = "near"
        geometry = "point"
    else:
        georel = "intersects"
        geometry = "polygon"

    # print(coords_values, georel, geometry)
    coordstring = ''
    for val in coords_values:
        if crs == "GeoJSON":
            val.reverse()
        coordstring += str(val[0]) + "," + str(val[1]) + ";"
    coordstring = coordstring.strip(";")

    url = "http://backend-orion:1026/v2/entities?type=" + entity_type
    if georel == "near":
        url += "&georel=near"
        url += ";maxDistance:" + str(maxDistance)
        url += "&geometry=" + geometry
        url += "&coords=" + coordstring
    elif georel in ["intersects", "coveredBy"]:
        url += "&georel=" + georel
        url += "&coords=" + coordstring
        url += "&geometry=" + geometry

# https://{{orion}}/v2/entities/?type=Building&georel=near;maxDistance:2000&geometry=point&coords=51.706774495,8.776277548

# https://{{orion}}/v2/entities/?type=Building&georel=intersects&coords=51.70683451303916,8.77602696418762;51.706462195326104,8.776386380195618;51.70663838176868,8.776847720146177;51.706965820787424,8.776482939720154;51.70683451303916,8.77602696418762&geometry=polygon
# GEOQUERY http://orion-backend:1026/v2/entities?type=Soil&georel=coveredBy&coords=-12.168005,-45.522538;-12.166836,-45.521848;-12.166294,-45.523917;-12.167643,-45.523918;-12.168005,-45.522538&geometry=polygon

    return url

def session_from_header_hash(hash):
    service, servicepath = hash.split("@")
    return session(service, servicepath)


def get_header_hash(request):
    
    headers = {}

    try:
        headers["Fiware-Servicepath"] = request.headers["fiware-servicepath"]
    except:
        raise HTTPException(status_code=400,
                            detail="Missing fiware-servicepath for query!")
    try:
        headers["Fiware-Service"] = request.headers["fiware-service"]
    except:
        raise HTTPException(status_code=400,
                            detail="Missing fiware-service for query!")

    return headers["Fiware-Service"] + "@" + headers["Fiware-Servicepath"]

def get_fiware_headers(request):
    
    headers = {}

    try:
        headers["Fiware-Servicepath"] = request.headers["fiware-servicepath"]
    except:
        raise HTTPException(status_code=400,
                            detail="Missing fiware-servicepath for query!")
    try:
        headers["Fiware-Service"] = request.headers["fiware-service"]
    except:
        raise HTTPException(status_code=400,
                            detail="Missing fiware-service for query!")

    return headers


def required_headers(Fiware_Servicepath: Annotated[str | None, Header()]  = "/", 
                  Fiware_Service : Annotated[str | None, Header()]  = "openiot"):
    return "Orion Header Checker"


def session(service="openiot", servicepath="/"):

    scope = {}
    scope["type"] = "http"
    scope["headers"] = []
    scope["headers"].append(["fiware-servicepath".encode(),servicepath.encode()])
    scope["headers"].append(["fiware-service".encode(),service.encode()])
    session = Request(scope=scope)

    return session


def set_state_source(body,state,source):
    body["state"]  = EntityState(state)
    body["source"] = EntitySource(source)
    return body

def infer_timestamp(time_index):
    
    if isinstance(time_index, int) or isinstance(time_index, float):   
        while time_index > 9999999999:
            time_index /= 10.
        return pd.to_datetime(time_index, unit='s').isoformat()
    
    if isinstance(time_index, str):   return pd.to_datetime(time_index).isoformat()
    if isinstance(time_index, datetime.datetime): return time_index.isoformat()
    if not time_index: return datetime.datetime.now().isoformat()
    return time_index.iso_format()



async def get_standard_attrs(entity_id,
        attrs: List[str] = None,
        time_index: str = None,
        jsondata: JSONStructure = None,):
    
    variables = {
        "entity_id": entity_id,
        "attrs": attrs,
        "time_index": time_index,
        "jsondata": jsondata,
    }

    return variables
                    