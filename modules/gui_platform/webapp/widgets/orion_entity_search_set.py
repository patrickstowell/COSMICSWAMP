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
        super().build_widget(store)
                
        # Check data is valid in store add default if not
        if "entity" not in store:
            store["entity"] = ""
        
        # Construct the main widget
        layout = html.Div([
            html.Div([
                html.Div(id="orion-entity-search-set-dummy"),
                html.Div(id="orion-entity-search-set-label", children="Entity Search :  ", className="input-widget-label"),
                dcc.Input(id="orion-entity-search-set-input", debounce=True, value=store["entity-search"], className="input-widget"),
                ], className="single-row-widget")
            ], style=jst("display: flex; flex-direction: column")
        )
        
        return layout
                
    def register_widget(self, app):
        super().register_widget(app)
    
        # Update the data store if path changed
        # @app.callback( 
        #             Output("store-entity-search","data"),
        #             Input("orion-entity-search-set-input","value")
        #         )
        # def set_entity(path):
        #     if not path: raise PreventUpdate  
        #     return path
            
        @app.callback( 
                    Output("store-entity-search","data"),
                    Output("orion-entity-search-set-input","value"),
                    Output("orion-entity-search-set-input","placeholder"),
                    Input("orion-entity-search-set-input","value")
                )
        def set_entity(path):
            if path == None: raise PreventUpdate  
            if path == "": raise PreventUpdate
            if path == " ": path = ""
            return path, "", path
        
        
        