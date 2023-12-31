import json
import json
import dash_core_components as dcc
from dash import Dash, html
from dash.dependencies import State, Input, Output
from directory_tool import *

default_store = {}
filename = "store_defaults.json"
if filename != "":
    default_store = json.load( open(get_assets() + filename, "r") )
    
def GetStoreDefaults():
    return default_store

def RegisterStore():
    
    store_objects = []
    for key in default_store:
        store_objects.append( dcc.Store(id=f"store-{key}", data=default_store[key], storage_type='local') )
        
        # store_objects.append( dcc.Store(id=f"store-{key}", data=default_store[key], storage_type='local') )
        
    # Build dash components
    header = html.Div(
        store_objects
    , id="store-header")
    
    return header

def GetStoreState():
    
    statelist = []
    for key in default_store:
        statelist.append( State( "store-" + key, "data") )
    return statelist

def FillStoreState(vals):
    statedict = {}
    for i, key in enumerate(default_store):
        statedict[key] = vals[i]
    return statedict