from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time


# Orion Service Chooser
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        
    def build_widget(self, store):
        super().build_widget(store)

        print("building service width")
                
        # Check data is valid in store add default if not
        if "Fiware-Service" not in store:
            store["Fiware-Service"] = "openiot"
        
        # Construct the main widget
        layout = html.Div([
            html.Div([
                html.Div(id="orion-service-set-dummy"),
                html.Div(id="orion-service-set-label", children="Service :  ", className="input-widget-label"),
                dcc.Input(id="orion-service-set-input", debounce=True, value=store["Fiware-Service"], className="input-widget"),
                ], className="single-row-widget")
            ], style=jst("display: flex; flex-direction: column")
        )
                
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        
        # Update the data store if path changed
        @app.callback( 
                    Output("store-Fiware-Service","data"),
                    Input("orion-service-set-input","value")
                )
        def set_path(path):
            if not path: raise PreventUpdate                
            return path
        
            
            
        
        
        