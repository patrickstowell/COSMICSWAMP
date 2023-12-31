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
        
    def get_gamma_pi(self, store, route):
        url = store["gammapi-deviceurl"] + "/" + route
        print("GAMMAPI", store, route, url)
        
        try:
            r = requests.get( url, timeout=1 )
        except:
            print("Python R Error", url)
            
            return {
                "error": "Connection Error"
            }
        if r.status_code > 400:
            print("STATUS CODE ERROR")
            return {
                "error": r.text
            }
            
        print("GAMMAPI", r.text)
            
        return r.json()
    
    def build_widget(self, store):
        """ Main Widget Construction, called on page updates.

        Args:
            store (dict): JSON Data Store Input

        Returns:
            html Layout Object: All outputs should be wrapped in a html.Div
        """
        super().build_widget(store)
        
        r = self.get_gamma_pi(store, "status")
        if "error" in r:
            return html.Div("Connection Error")
        
        valid = "running" in r
        state = False
        if valid: 
            state = r["running"]
            
        # Construct the main widget
        layout = html.Div([
            html.Div([
                dcc.Interval(id="gammapi-startstop-interval",interval=1000),
                html.Div(id="gammapi-startstop-controldummy"),
                html.Div(id="gammapi-startstop-button", children=[
                    html.Button("Start", id='gammapi-startstop-button-start', disabled=state and valid),
                    html.Button("Stop", id='gammapi-startstop-button-stop', disabled=~state and valid)
                    ], className="gammapi-startstop-button-container"),
                html.Div("Run Time : "),
                html.Div("00:00:00", id="gammapi-startstop-runtime")
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
            Output("gammapi-startstop-controldummy", "children"),
            Input("gammapi-startstop-button-start","n_clicks"),
            State("store-gammapi-deviceurl","data")
        )
        def start_run(n, path):
            if not n: raise PreventUpdate
            store = GetStoreDefaults()
            store["gammapi-deviceurl"] = path   
            r = self.get_gamma_pi(store, "start")            
            return ""   
        
        @app.callback(
            Output("gammapi-startstop-controldummy", "disabled"),
            Input("gammapi-startstop-button-stop","n_clicks"),
            State("store-gammapi-deviceurl","data")
        )
        def stop_run(n, path):
            if not n: raise PreventUpdate
            store = GetStoreDefaults()
            store["gammapi-deviceurl"] = path   
            r = self.get_gamma_pi(store, "stop")            
            return True        
        
        @app.callback(
            Output("gammapi-startstop-button-start", "disabled"),
            Output("gammapi-startstop-button-stop", "disabled"),
            Output("gammapi-startstop-runtime", "children"),
            Input("gammapi-startstop-interval","n_intervals"),
            State("store-gammapi-deviceurl","data")
        )
        def get_runtime(n, path):
            if not n and not nclick: raise PreventUpdate
            
            store = GetStoreDefaults()
            store["gammapi-deviceurl"] = path   
            r = self.get_gamma_pi(store, "status")
            runt = "0"
            if "runtime" in r:
                runt = r["runtime"]
            if "running" in r and r["running"]:
                return True, False, runt
            if "running" in r and not r["running"]:
                return False, True, runt         
            return True, True, "?"
        
        # @app.callback(
        #     Output("gammapi-startstop-button-start", "disabled"),
        #     Output("gammapi-startstop-button-stop", "disabled"),
        #     Input("gammapi-startstop-button-stop","n_clicks"),
        #     State("store-gammapi-deviceurl","data")
        # )
        # def start_run(n, path):
        #     if not n: raise PreventUpdate
        #     store = GetStoreDefaults()
        #     store["gammapi-deviceurl"] = path   
        #     r = self.get_gamma_pi(store, "stop")
        #     if "running" in r and not r["running"]:
        #         return False, True
        #     raise PreventUpdate
        
        