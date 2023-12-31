from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time
# Simple Box Plugin
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        print("Building Gamma Pi Run Control", config)
        
        self.daq_url = 'http://gammapi.local:8080'
        
    def build_widget(self):
        print("Building Widget")
        
        layout = html.Div([
            html.Div(id="gammapi-runcontrol-dummy"),
            dcc.Interval(id="gammapi-runcontrol-interval", interval=5000),
            html.Div([
                html.Button("Start Run",id="gammapi-runcontrol-start"),
                html.Button("Stop Run",id="gammapi-runcontrol-stop"),
                dcc.Loading(
                id="loading-1",
                type="default",
                children=html.Button("Stopped",id="gammapi-runcontrol-running", disabled=False, className='gammapi-stopped')
                )
            ], className="row-central"),
            
            html.Div([
                html.Div("Run Time : ", className='stopped'),
                html.Div("--:--:--", id="gammapi-runcontrol-runtime")
            ], style=jst("display: flex, flex-direction: row"))
        ], style=jst("display: flex, flex-direction: column"))
        
        return layout
                
    def register_widget(self, app):
        super().register_widget(app)
        print("Registering Widget")
        
        
        # @app.callback( 
        #             Output("gammapi-runcontrol-running","className"),
        #             Output("gammapi-runcontrol-running","children"),
        #             Output("gammapi-runcontrol-start","disabled"),
        #             Output("gammapi-runcontrol-start","className"),
        #             Output("gammapi-runcontrol-stop","disabled"),
        #             Output("gammapi-runcontrol-stop","className"),
        #             Input("gammapi-runcontrol-interval","n_intervals")
        #         )
        # def check_interval(nint):
        #     if not nint: raise PreventUpdate    
            
        #     url = f'{self.daq_url}/status'
        #     response = requests.get(url)
        #     values = response.json()[0]
        #     print(values)
            
        #     if values["running"]:
        #         return "gammapi-running", "Running", True, "gammapi-disabled", False, "gammapi-enabled", "Loaded"
        #     else:
        #         return "gammapi-stopped", "Stopped", False, "gammapi-enabled", True, "gammapi-disabled", "Loaded"

            
        @app.callback( 
                    Output("gammapi-runcontrol-start","disabled"),
                    Output("gammapi-runcontrol-start","className"),
                    Output("gammapi-runcontrol-stop","disabled"),
                    Output("gammapi-runcontrol-stop","className"),
                    Output("loading-output-1","children"),
                    Input("gammapi-runcontrol-stop","n_clicks")
                )
        def start_run(nstop):
            if not nstop: raise PreventUpdate    
            print("Stoppgin run")
            url = f'{self.daq_url}/stop'
            response = requests.get(url, timeout=30)
            values = response.json()
            button = html.Button("STOPPED",id="gammapi-runcontrol-running", disabled=False, className='gammapi-stopped')
            return False, "gammapi-enabled", True, "gammapi-disabled", button
            
        @app.callback( 
                    Output("gammapi-runcontrol-start","disabled"),
                    Output("gammapi-runcontrol-start","className"),
                    Output("gammapi-runcontrol-stop","disabled"),
                    Output("gammapi-runcontrol-stop","className"),
                    Output("loading-output-1","children"),
                    Input("gammapi-runcontrol-start","n_clicks")
                )
        def start_run(nstart):
            if not nstart: raise PreventUpdate    
            print("starting run")
            url = f'{self.daq_url}/start'
            
            try:
                response = requests.get(url, timeout=30)
                values = response.json()
                button = html.Button("RUNNING",id="gammapi-runcontrol-running", disabled=False, className='gammapi-running')
                return True, "gammapi-disabled", False, "gammapi-enabled", button
            except:
                print("ERROR")
                
            button = html.Button("ERROR",id="gammapi-runcontrol-running", disabled=False, className='gammapi-error')
            return False, "gammapi-enabled", True, "gammapi-disabled", button
                
                
            
            
        
            
            
        
        
        