from fastapi import FastAPI, HTTPException
from typing import Union

from fastapi import FastAPI, Request
from fastapi import FastAPI, Header
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from typing import Annotated
from fastapi import FastAPI, Query

import os
import requests
import json
import logging

import pandas as pd
from typing import List


def query_attrs(vals):
    val_str = ""
    
    for v in vals:
        v = v.replace(";",",")
        v = v.replace("&&",",")
        v = v.replace("&",",")
        v = v.replace(" AND ",",")
        for vi in v.split(","):
            if len(val_str) > 0: val_str += ", "
            val_str += str(vi).lower()
    return val_str

def query_table_from_headers_and_type(headers,entity_type):
    service = headers["Fiware-Service"]
    service_path = headers["Fiware-Servicepath"]

    return f' FROM "mt{service}"."et{entity_type}" WHERE fiware_servicepath=\'{service_path}\''
    
def query_entity(entity_id):
    return f" AND entity_id='{entity_id}'"

def query_cut_filter(cuts):
    cut_str = " "
    if not cuts: return ""
    for c in cuts:

        c = c.replace(","," AND ")
        c = c.replace(";"," AND ")
        c = c.replace("&&"," AND ")
        c = c.replace("&"," AND ")

        cut_str += " AND "
        cut_str += c
    return cut_str

def query_groupby_filter(groupBy=None):
    if groupBy: return f" GROUP BY {groupBy}"
    return ""

def query_orderby_filter(orderBy=None, ascending=True):
    val_str = ""
    if not orderBy: return val_str
    
    val_str = f" ORDER BY {orderBy}"
    if ascending: val_str += " ASC"
    else: val_str += " DESC"

    return val_str

def query_limit_filter(limit=100):
    return f"LIMIT {limit}"

def query_retrieve_pandas(sql, url):

    # Remove rows with NA.
    print("RETRIEVING", sql, url)
    df = pd.read_sql(sql,  url)
    return [row.dropna().to_dict() for index,row in df.iterrows()]
  
