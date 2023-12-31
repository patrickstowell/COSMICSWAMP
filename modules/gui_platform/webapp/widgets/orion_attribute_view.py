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
from dash_core_components import Interval, Textarea

import modules.iot_platform.cosmicswamp as cosmicswamp

# Orion Entity Viewer Plugin
class plugin(base_plugin):

    def __init__(self, config, app):
        super().__init__(config)        
        
    def build_widget(self, store):
        super().build_widget(store)
        
        self.service = store["Fiware-Service"]
        self.servicepath = store["Fiware-Servicepath"]
        
        table, complex = self.build_meta_table(store)
        layout = html.Div([
            html.Div([
                html.Div("Entity List : ", style=jst("padding-right: 10px;")),
                html.Div(f"[ {self.service} : {self.servicepath} ]", style=jst("padding-left: 10px; color: blue;"))
            ], style=jst("width: 100%; padding: 5px; display: flex; flex-direction: row")),
            html.Div([
                html.Div(table, style=jst("padding: 20px; width: 100%;"))
                ], style=jst("width: 100%; flex-grow: 1; padding: 5px; display: flex; flex-direction: row")),
            html.Div([
                html.Div(complex, style=jst("padding: 20px; width: 100%;"))
                ], style=jst("width: 100%; flex-grow: 1; padding: 5px; display: flex; flex-direction: row"))
            ], style=jst("display: flex; padding: 5px; flex-direction: column")
        )

        return layout
                
    def build_meta_table(self, store):

        session = cosmicswamp.get_session_from_dict(store)
        entity_id = store["entity-selected"]
        vals = cosmicswamp.get_current_entity_from_id(session, entity_id)
        
        complex_attrs = []

        # Convert Entities to a list of object
        ids = []
        types = []
        values = []

        
        

        for key in vals:
            if key == "id": continue
            if key == "type": continue
            
            if vals[key]["type"] in ["DateTime","Integer","Number","String","Text"]:
                ids.append( key )
                types.append( vals[key]["type"] )
                values.append( vals[key]["value"] )
            else:
                c_key = key
                c_type = vals[key]["type"]
                c_value = vals[key]["value"]
                complex_attrs.append(html.Div([
                        html.Div([
                            html.Div("Attribute : ", style=jst("padding-right: 5px;")),
                            html.Div(f"[ {c_key} : {c_type} ]", style=jst("padding-left: 10px; color: blue;")),
                            html.Button("Commit", id={"type": "commit-button", "index": c_key}, n_clicks=0)
                        ], style=jst("width: 100%; padding: 5px; padding-bottom: 0px; display: flex; flex-direction: row")),
                        html.Div(
                            Textarea( value=json.dumps(c_value, indent=4), id=f"attribute-view-text-{c_key}", style={ "min-width":"50px", "width":"100%", "min-height":"150px", "display":"flex", "flex-grow": 12} ),
                            style=jst("width: 100%; padding: 5px; padding-bottom: 0px; display: flex; flex-direction: row")
                        )
                    ])
                )

                
        # Build a pandas data frame and sort by type and id
        rundata = pd.DataFrame( data= {"id": ids, "type":types, "value": values} )
            
        rundata = rundata.sort_values(["type","id"])
        
        # Keep a local copy in the store of all entities
        self.entitylist = rundata
                        
        return dash_tools.simple_pandas_table( rundata, "data-attribute-table" ), complex_attrs
    
    
    def register_widget(self, app):
        super().register_widget(app)

        # Widget refresh on a local store update.
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-entity-selected","data"),
            Input("store-Fiware-Service","data"),
            Input("store-Fiware-Servicepath","data")
        )
        def refresh_custom(search, service, path):
            store = GetStoreDefaults()
            store["entity-selected"] = search
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            return self.build_widget(store)
        
                    
        @app.callback(
            Output("store-attribute-selected","data"),
            Input("data-attribute-table", "active_cell"),
        )
        def select(cell):
            print("Cell selected")
            if not cell: return "NONE"
            return cell["row_id"]
    