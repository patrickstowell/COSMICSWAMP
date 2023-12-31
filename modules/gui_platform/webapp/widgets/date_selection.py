from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time

# Orion Entity Chooser via Text
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
                
        # Check data is valid in store add default if not
        if "entity" not in store:
            store["entity"] = ""
        
        # Construct the main widget
        layout = html.Div([
            html.Div([
                html.Div(id="data_selection-dummy"),
                html.Div(id="data_selection-label", children="Date : ", style=jst("padding-top: 8px; padding-right: 10px")),
                dcc.DatePickerRange(id='date-start'),
                ], style=jst("padding: 5px; display: flex; flex-direction: row"))
            ], style=jst("display: flex; flex-direction: column")
        )
        
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        
        # # Update the data store if path changed
        # @app.callback( 
        #             Output("store-local","data"),
        #             Input("data_selection-input","value"),
        #             State("store-local","data")
        #         )
        # def set_path(path, store):
        #     if not path: raise PreventUpdate    
        #     store["entity"] = path
            
        #     return store
        
            
            
        
        
        