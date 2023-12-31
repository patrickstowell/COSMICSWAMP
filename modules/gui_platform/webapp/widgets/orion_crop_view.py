from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time
from orion_handler import *
from dash_tools import *
import pandas as pd
from static_store import *

import modules.iot_platform.cosmicswamp as cosmicswamp

# Orion Entity Viewer Plugin
class plugin(base_plugin):

    def __init__(self, config, app):
        super().__init__(config)        
        
    def build_widget(self, store):
        super().build_widget(store)
        
        self.service = store["Fiware-Service"]
        self.servicepath = store["Fiware-Servicepath"]
        
        layout = html.Div([
            html.Div([
                html.Div("Entity List : ", style=jst("padding-right: 10px;")),
                html.Div(f"[ {self.service} : {self.servicepath} ]", style=jst("padding-left: 10px; color: blue;"))
            ], style=jst("width: 100%; padding: 5px; display: flex; flex-direction: row")),
            html.Div([
                html.Div(self.build_meta_table(store), style=jst("padding: 20px; width: 100%;"))
                ], style=jst("width: 100%; flex-grow: 1; padding: 5px; display: flex; flex-direction: row"))
            ], style=jst("display: flex; padding: 5px; flex-direction: column")
        )

        return layout
                
    def build_meta_table(self, store):

        session = cosmicswamp.get_session_from_dict(store)
        vals = cosmicswamp.get_all_current_entity_ids(session, limit=1000)
        
        # Convert Entities to a list of object
        ids = []
        types = []

        for i, value in enumerate(vals):
            ids.append( value["id"] )
            types.append( value["type"] )
                
        # Build a pandas data frame and sort by type and id
        rundata = pd.DataFrame( data= {"id": ids, "type":types} )

        print("PANDAS START", ids, len(ids))
        if "entity-search" in store and store["entity-search"] != "":                        
            rundata = rundata[rundata["id"].str.contains(store["entity-search"])]

        if "type-search" in store and store["type-search"] != "":                        
            rundata = rundata[rundata["type"].str.contains(store["type-search"])]

        rundata = rundata.sort_values(["type","id"])

        # Keep a local copy in the store of all entities
        self.entitylist = rundata
                        
        return dash_tools.simple_pandas_table( rundata, "data-entity-table" )
    
    
    def register_widget(self, app):
        super().register_widget(app)

        # Widget refresh on a local store update.
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-entity-search","data"),
            Input("store-type-search","data"),
            Input("store-Fiware-Service","data"),
            Input("store-Fiware-Servicepath","data")
            )
        def refresh_custom(search, types, service, path):
            store = GetStoreDefaults()
            store["entity-search"] = search
            store["type-search"] = types
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            return self.build_widget(store)
        
                    
        @app.callback(
            Output("store-entity-selected","data"),
            Input("data-entity-table", "active_cell"),
        )
        def select(cell):
            print("Cell selected")
            if not cell: return "NONE"
            return cell["row_id"]
    