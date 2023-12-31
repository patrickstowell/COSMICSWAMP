from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time



# Orion Path Chooser
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        
    def build_widget(self, store):
        super().build_widget(store)
                
        print("BUILDING ORION WIDGET")
        # Check data is valid in store add default if not
        if "Fiware-Servicepath" not in store:
            store["Fiware-Servicepath"] = "/"
        
        # Construct the main widget
        layout = html.Div([
            html.Div([
                html.Div(id="orion-path-set-dummy"),
                html.Div(id="orion-path-set-label", children="Service Path :  ", className="input-widget-label"),
                dcc.Input(id="orion-path-set-input", debounce=True, placeholder=store["Fiware-Servicepath"], className="input-widget"),
                ], className="single-row-widget")
            ]
        )
        
        return layout
                
                    
    def register_widget(self, app):
        super().register_widget(app)

        # Update the data store if path changed
        @app.callback( 
                    Output("store-Fiware-Servicepath","data"),
                    Input("orion-path-set-input","value")
                )
        def set_path(path):
            if not path: raise PreventUpdate  
            return path