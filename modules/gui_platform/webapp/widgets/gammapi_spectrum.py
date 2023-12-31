from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time

from static_store import *
import plotly.graph_objects as go
import numpy as np
# Orion Path Chooser
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        
    def get_gamma_pi(self, store, route):
        url = store["gammapi-deviceurl"] + "/" + route
        
        r = requests.get( url, timeout=10 )
        if r.status_code > 400:
            return {
                "error": r.text
            }
            
        return r.json()
    
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
                html.Div(id="gammapi-spectrum-total-parent", children=[
                    html.Button("Refresh", id='gammapi-spectrum-total-refresh'),
                    self.build_spectrum_plot(store)
                    ], className="gammapi-spectrum-total-parent"),
                ])
            ], style=jst("display: flex; flex-direction: column")
        )
        
        return layout
                
    def build_spectrum_plot(self, store):
        
        data = self.get_gamma_pi( store, "hits" )
        runi = self.get_gamma_pi( store, "run")
        
        for i in range(1000,1024):
            data["0"]["parent"][i] = 0
            data["1"]["parent"][i] = 0
            data["0"]["slice"][i] = 0
            data["1"]["slice"][i] = 0
            
        
        xvals = np.linspace(0,1024.0,1024)
        
        binrange = dict(start=0, end=1024, size=1)
        parentexp = float(runi["1"]["parent_stop"]-runi["1"]["parent_start"])
        sliceexp = float(runi["1"]["slice_stop"]-runi["1"]["slice_start"])
        
        
        # histogram1 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
        #                         y=data['0']["parent"], name="Dev-0-Total" )
        # histogram2 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
        #                         y=data['0']["slice"], name="Dev-0-Slice" )
        # histogram3 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
        #                         y=data['1']["parent"], name="Dev-1-Total" )
        # histogram4 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
        #                         y=data['1']["slice"], name="Dev-2-Slice" )
        
        histogram1 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
                                y=np.array(data['0']["parent"])/parentexp, name="Rate-0-Total" )
        histogram2 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
                                y=np.array(data['0']["slice"])/sliceexp, name="Rate-0-Slice" )
        histogram3 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
                                y=np.array(data['1']["parent"])/parentexp, name="Rate-1-Total" )
        histogram4 = go.Histogram( x=xvals, xbins=binrange, autobinx=False, histfunc="sum",
                                y=np.array(data['1']["slice"])/sliceexp, name="Rate-2-Slice" )
        fig = go.Figure(histogram1)
        # fig.add_trace(histogram2)
        fig.add_trace(histogram3)
        # fig.add_trace(histogram4)
        fig.update_yaxes(type="log", title="Counts")
        fig.update_xaxes(range=(0,1024), title="ADC Value")
        fig.update_layout(barmode='overlay')
        fig.update_traces(opacity=0.75)
        graph = dcc.Graph(id=f'{self.id}-spectrum', figure=fig, style={"width":"100%","height":"40vh"})
        
        fig2 = go.Figure(histogram2)
        fig2.add_trace(histogram4)
        fig2.update_yaxes(type="log", title="Counts")
        fig2.update_xaxes(range=(0,1024), title="ADC Value")
        fig2.update_layout(barmode='overlay')
        fig2.update_traces(opacity=0.75)
        graph2 = dcc.Graph(id=f'{self.id}-spectrum2', figure=fig2, style={"width":"100%","height":"40vh"})



        return html.Div([graph, graph2])

    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        
        
        # Update the data store if path changed
        @app.callback( 
                    Output(self.id + "-box", "children"),
                    Input("gammapi-spectrum-total-refresh","n_clicks"),
                    Input("store-gammapi-deviceurl","data")
                )
        def set_path(n, path):
            if not path or not n: raise PreventUpdate  
            store = GetStoreDefaults()
            store["gammapi-deviceurl"] = path                        
            return self.build_widget(store)
        
