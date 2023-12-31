from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time
import pandas as pd
import numpy as np

# Orion Entity Chooser via Text
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        self.crate_url = config["data"]["crate_url"]
        self.sql_query = config["data"]["sql_query"]
        
        
    def build_figure(self, sql_query):
        
        headers = {
            "Fiware-Service": "openiot",
            "Fiware-Servicepath": "/lanapre_pilot"
            }
        data = {
            "stmt": sql_query
        }
        print(self.crate_url, self.data)
        r = requests.get(self.crate_url + "/_sql", headers=headers, json=data)
        vals = r.json()  
        
        if "rows" not in vals:
            print("ERROR IN CRATE CHECK")
            return ""
        
        df = pd.DataFrame(data=vals["rows"], columns=vals["cols"])
        
        import plotly.graph_objects as go
        x_name = vals["cols"][0]
        fig = ""
        for i, colname in enumerate(vals["cols"]):
            
            # if colname.lower() == "time":
                
            #     df[colname] = pd.to_datetime(np.int(df[colname]), unit='s')
            
            if i == 0: continue
            y_name = colname
            plot = go.Scatter(x = df[x_name], y=df[y_name], name=y_name )
            if i == 1:
                fig = go.Figure(plot)
            else:
                fig.add_trace( plot )
        
        fig.update_layout(margin=dict(t=10, r=10))
        
        return dcc.Graph(id=f'{self.id}-graph', figure=fig)

        
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
                html.Div(id=f"{self.id}-dummy"),
                
                html.Div([
                    html.Div([
                    html.H6("TEST"),
                ], style=jst("padding: 0px; width: 50%; display: flex; flex-direction: row; justify-content: left;")),
                                
                html.Div([
                    html.Button("Run Query", id=f"{self.id}-run-button"),
                    html.Button("Show Query", id=f"{self.id}-show-button")
                ], style=jst("padding: 0px; width: 50%; display: flex; flex-direction: row; justify-content: right;")),
                
                ], style=jst("padding: 5px; display: flex; flex-direction: row;") ),
                
                html.Div(
                        dcc.Textarea(id=f"{self.id}-text", value=self.sql_query,  style=jst("width: 100%; display: flex; flex-grow: 1; min-height: 200px; max-height: 100%;")),
                        hidden=True,
                        id=f"{self.id}-text-parent",
                        style=jst("width: 99%; min-height: 200px; max-height: 1000px")),
                
                html.Div(
                    id=f"{self.id}-plot-parent",
                    children=self.build_figure(self.sql_query)
                )
            ], style=jst("display: flex; flex-direction: column; width: 100%"))
        
        
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        
        print("WIDGETS REGISTERED WITH ", f"{self.id}-dummy")
        # Update the data store if path changed
        @app.callback( 
                    Output(f"{self.id}-plot-parent","children"),
                    Input(f"{self.id}-run-button","n_clicks"),
                    State(f"{self.id}-text","value")
                )
        def set_text(n, path):
            if not n: raise PreventUpdate
            
            self.sql_query = path
            print("SQL Query")
            print('---------')
            print(self.sql_query)
            print('---------')
            return self.build_figure(self.sql_query)
        
        @app.callback( 
                    Output(f"{self.id}-text-parent","hidden"),
                    Output(f"{self.id}-show-button","children"),
                    Input(f"{self.id}-show-button","n_clicks"),
                    State(f"{self.id}-show-button","children"),
                    State(f"{self.id}-show-button","n_clicks")
                    )
        def set_text2(n, state, n2):
            if not n: raise PreventUpdate
            if not state: raise PreventUpdate
            
            print("SET TEXT", n, state, n2)
            if state == "Show Query":
                return False, "Hide Query"
            if state == "Hide Query":
                return True, "Show Query"
            
            raise PreventUpdate
        
        
            
            
        
        
        