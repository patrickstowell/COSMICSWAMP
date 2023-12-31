import os
import requests
import json
import logging
import pandas as pd
from typing import List
import time
import datetime
from fastapi.encoders import jsonable_encoder


def format_id(entity_id):
    if (not entity_id.startswith("urn:") and 
        not entity_id.startswith("uri:")):

        if "ngsi-ld:" in entity_id:
            entity_id = "urn:" + entity_id
        else:
            entity_id = "urn:ngsi-ld:" + entity_id

    return entity_id


def update_from_attr(ngsi, attrs):

    if not attrs: return ngsi
    
    for a in attrs:
        ask, asv = a.split("=")
        try:
            ngsi[str(ask)] = eval(asv, {}, {})
        except:
            ngsi[str(ask)] = asv

    return ngsi


def dict_keys_to_str(dt):
    return json.loads(json.dumps(dt))


def check_format(body, entity_id=None, entity_type=None):
    if not body:
        body = {}

    if "id" not in body and entity_id: body["id"] = entity_id
    if "type" not in body and entity_type: body["type"] = entity_type

    if "TimeInstant" not in body:
        body["TimeInstant"] = {"value": datetime.datetime.now().isoformat(), "type": "DateTime"}

    return body


def update_time_index(ngsi, time_index):
    if not time_index: return ngsi
    ngsi["TimeInstant"] = {"value": time_index, "type": "DateTime"}
    return ngsi

def update_datetime(ngsi, dt):
    if not dt: return ngsi
    ngsi["TimeInstant"] = {"value": dt.isoformat(), "type": "DateTime"}
    return ngsi

def coerce_data(body):

    body = json_compatible_item_data = jsonable_encoder(body)


    for key in body:
        if key == "id": continue
        if key == "type": continue
        if not isinstance(body[key], dict):
            body[key] = { "value": body[key], "type": "Number" } 
        if body[key] == None: del body[key]

    if "location" in body:
        if "type" not in body["location"]: body["location"]["type"] = ""
        if body["location"]["type"] != "geo:json":
            temploc = {"type": "geo:json", "value": body["location"].copy()}
            body["location"] = temploc

    return body


def check(body):
    badkeys = []
    for key in body:
        if key in ["id", "type"]: continue
        if body[key]["value"] == None: badkeys.append(key)

    for key in badkeys:
        del body[key]

    return json.loads(json.dumps(body,allow_nan=False))



def set_default(body, key, value):

    datain = {key:value}
    datain = coerce_data(datain)

    for key in datain:
        if key not in body: 
            body[key] = datain[key]

    return body

def set_override(body, key, value):
    if not value: return body

    datain = {key:value}
    datain = coerce_data(datain)

    for key in datain:
        body[key] = datain[key]

    return body

def set_value(body, key, value):
    if not value: return body

    datain = {key:value}
    datain = coerce_data(datain)

    for key in datain:
        body[key] = datain[key]

    return body

def compile_entity(body, entity_id, entity_type, time_index, attrs):
    body = dict_keys_to_str(body)
    body = check_format(body, entity_id, entity_type)
    body = update_time_index(body, time_index)
    body = update_from_attr(body, attrs)
    body = coerce_data(body)
    return body

def pretty_print(dict):
    print("Entity - ", dict["id"], dict["type"])
    for key in dict:
        if key in ["id","type"]: continue
        print(" -> ", key, dict[key]["type"], dict[key]["value"])

import numpy as np

def mean(data):

    if len(data) == 0: return {}

    newdata = data[0].copy()

    for key in newdata:
        if key == "id" or key == "type": continue

        if not (isinstance(newdata[key]["value"], float) or isinstance(newdata[key]["value"],int)):
            continue

        newvals = []
        for i in range(len(data)):
            newvals.append( data[i][key]["value"] )

        meanval = np.mean(np.array(newvals))

        newdata[key]["value"] = meanval

    return newdata

import time
import datetime
import scipy

def interpolate_df(df, time_index, key):
    unix = time.mktime(time_index.timetuple())
    df["unix"] = df["date"].astype(int) / 10**9
    func = scipy.interpolate.interp1d( df["unix"], df[key] )
    return func(unix)
