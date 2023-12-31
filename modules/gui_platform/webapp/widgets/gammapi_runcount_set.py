from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time

from static_store import *

# Orion Path Chooser
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        
    def build_widget(self, store):
        """ Main Widget Construction, called on page updates.

        Args:
            store (dict): JSON Data Store Input

        Returns:
            html Layout Object: All outputs should be wrapped in a html.Div
        """
        super().build_widget(store)
        
            
        # Construct the main widget
        layout = html.Div([
            html.Div([
                html.Div("Run Count : "),
                dcc.Input(id="gammapi-runcount-input", debounce=True)
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
                    Output(self.id + "-box", "children"),
                    Input("store-gammapi-deviceurl","data")
                )
        def set_path(path):
            if not path: raise PreventUpdate  
            store = GetStoreDefaults()
            store["gammapi-deviceurl"] = path                        
            return self.build_widget(store)
        
        @app.callback(
            Output("store-gammapi-runcount","data"),
            Input("gammapi-runcount-input","value")
        )
        def runcount(n):
            if not n: raise PreventUpdate
            return int(n)
        
        