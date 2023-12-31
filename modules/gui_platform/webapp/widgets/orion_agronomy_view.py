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
        
        agronomy_data = self.build_data(store)
        layout = html.Div([
            html.Div([
                html.Div(agronomy_data, style=jst("padding: 20px; width: 100%;"))
                ], style=jst("width: 100%; flex-grow: 1; padding: 5px; display: flex; flex-direction: row"))
            ], style=jst("display: flex; padding: 5px; flex-direction: column")
        )

        return layout
                
    def build_data(self, store):

        session = cosmicswamp.get_session_from_dict(store)
        entity_id = store["agronomy-selected"]
        
        if entity_id == "": return html.Div("Select Agronomy to Display", className="begin-info")
        vals = cosmicswamp.get_current_entity_from_id(session, entity_id)


        # Build table top left for main variables [creation date, name, id, variety_name]
        # Sowing and harvest dates
        # Max duration
        children = {
            html.Div("Entity"), 
        }


        # Two large numbers
        # Irrigation prescription (total to date, link to irrigation window)
        # Nitrogen total to date (link to nitrogen window)

        # Zone growth
        # Plot of time series with associated zones soil moisture within agro map between start and end date
        


        children = []
        for entry in vals:
            print(entry)
            children.append(html.Div(entry))
                                
        return html.Div(children, className="agronomy-view")
    
    
    def register_widget(self, app):
        super().register_widget(app)

        # Widget refresh on a local store update.
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-agronomy-selected","data"),
            Input("store-Fiware-Service","data"),
            Input("store-Fiware-Servicepath","data")
        )
        def refresh_custom(search, service, path):
            print("AGRNOMY UPDATE", search)
            store = GetStoreDefaults()
            store["agronomy-selected"] = search
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            return self.build_widget(store)
    