from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval, Textarea
import time
from orion_handler import *
from dash_tools import *
import pandas as pd
from static_store import *

from dash import Dash, dcc, html, Input, Output, ALL
from static_store import *

# Orion Entity Viewer Plugin
class plugin(base_plugin):
    
    
    def __init__(self, config, app):
        # Call base parameter set
        super().__init__(config)
        self.app = app
        self.complexlist = []
        
        self.attribute_object_list = {}
        
        
    def build_widget(self, store):
        """ Main Widget Construction, called on page updates.

        Args:
            store (dict): JSON Data Store Input

        Returns:
            html Layout Object: All outputs should be wrapped in a html.Div
        """
        super().build_widget(store)
                
        # Check data is valid in store add default if not
        if "entity_selected" not in store:
            store["entity_selected"] = ""
            
        entity_name = store["entity_selected"]
        
        add_register(self.id, "update")
        
        layout = html.Div([
            html.Div([
                html.Div("Attributes : ", style=jst("padding-right: 10px;")),
                html.Div(f"[ {entity_name} ]", style=jst("padding-left: 10px; color: blue;"))
            ], style=jst("width: 100%; padding: 5px; padding-bottom: 0px; display: flex; flex-direction: row")),
            html.Div([
                html.Div(self.build_meta_table(store), style=jst("padding: 20px; width: 100%;"))
                ], style=jst("width: 100%; flex-grow: 1; padding: 5px; display: flex; flex-direction: row"))
            ], style=jst("display: flex; padding: 5px; padding-top: 0px; flex-direction: column")
        )

        return layout
                
    def build_meta_table(self, store):
        session = cosmicswamp.get_session_from_dict(store)
        vals = cosmicswamp.get_all_current_entity_ids(session)

        objects = []
        
        
        # Setup ORION Call
        if store["entity_selected"] == "NONE":
            return objects
        
        if "entity_selected" not in store:
            store["entity_selected"] = ""
        
        entity_name = store["entity-selected"]
        
        ORION.service = store["Fiware-Service"]
        ORION.servicepath = store["Fiware-Servicepath"]
        vals = ORION.get_entity_attrs(entity_name)
        if 'error' in vals:
            return "Cannot access entity"
        
        # Convert Entities to a list of object
        names = []
        types = []
        values = []
        complex = {}
        
        for key in vals:
            if key == "id": continue
            if key == "type": continue

            if vals[key]["type"] not in ["Integer", "Number","Text","Relationship","DateTime"]:
                complex[key] = ( vals[key] )
                continue
            
                
            print('ngsi', vals[key])
            names.append( key )
            types.append( vals[key]["type"] )
            values.append( vals[key]["value"] )
            
                
        # Build a pandas data frame and sort by type and id
        rundata = pd.DataFrame( data= {"ID": names, "TYPE":types, "VALUE": values} )            
        rundata = rundata.sort_values(["TYPE","ID"])
        
        # Keep a local copy in the store of all entities
        if len(rundata) > 0:
            
            # if 'standard' not in self.attribute_object_list:
            self.attribute_object_list["standard"] = html.Div([
                html.Div([
                    html.Div(id="attribute-view-commit-standard-dummy"),
                    html.Div("Standard Attributes : ", style=jst("padding-right: 5px;")),
                    html.Button("Commit", id={"type": "commit-button", "index": "standard"}, n_clicks=0)
                    
                ], style=jst("width: 100%; padding: 5px; padding-bottom: 0px; display: flex; flex-direction: row")),
                ( dash_tools.simple_pandas_table( rundata, "data-attribute-table" ) )
            ])
                
            objects.append(self.attribute_object_list["standard"])
            add_register(self.id, "standard")
            
            app = self.app
            
        self.complexlist = complex
        for c_key in complex:
            
            if c_key not in global_register:
                global_register[c_key] = False
                
            c = complex[c_key]
            c_type = c["type"]
            c_value = c["value"]
            
            
            # if c_key not in self.attribute_object_list:
            self.attribute_object_list[c_key] = html.Div([
                html.Div([
                    html.Div("Attribute : ", style=jst("padding-right: 5px;")),
                    html.Div(f"[ {c_key} : {c_type} ]", style=jst("padding-left: 10px; color: blue;")),
                    html.Button("Commit", id={"type": "commit-button", "index": c_key}, n_clicks=0)
                ], style=jst("width: 100%; padding: 5px; padding-bottom: 0px; display: flex; flex-direction: row")),
                html.Div(
                    Textarea( value=json.dumps(c_value, indent=4), id=f"attribute-view-text-{c_key}", style={ "min-width":"700px", "display":"flex", "flex-grow": 12} ),
                    style=jst("width: 100%; padding: 5px; padding-bottom: 0px; display: flex; flex-direction: row")
                )
            ])
                
            add_register(self.id, c_key)
            objects.append(self.attribute_object_list[c_key])
    
        self.register_complex()
            
        return html.Div(
            objects
        )
        
    
    
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        self.app = app
        
        
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-entity-selected","data"),
            Input("store-Fiware-Service","data"),
            Input("store-Fiware-Servicepath","data")
        )
        def refresh_custom(entity, service, path):
            store = GetStoreDefaults()
            print("ENTITY", entity)
            store["entity-selected"] = entity
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            return self.build_widget(store)
            # raise PreventUpdate
            
        self.register_complex()
        
        
    
    def register_complex(self):
            
        app = self.app
        
        # if needs_register(self.id, "standard"):

            
                
        # print("ADDING COMPLEX")
        # for c_key in self.complexlist:
        #     if c_key == "standard": continue
        #     print("Checking COMPLEX : ", c_key, global_register[c_key])
        #     if global_register[c_key]: continue
        #     print("REGISTERED COMPLEX : ", c_key)
        #     @app.callback(
        #         Output(self.id + "-box", "children"),
        #         Input(f"attribute-view-commit-{c_key}", "n_clicks"),
        #         State(f"attribute-view-text-{c_key}", "value"),
        #         State(f"attribute-view-text-{c_key}", "id"),
        #         State("store-local", "data")
        #     )
        #     def update_complex(n, text, id, store):
        #         print("Updating complex : {id}")
        #         return self.build_widget(store)
            
        #     global_register[c_key] = True

        