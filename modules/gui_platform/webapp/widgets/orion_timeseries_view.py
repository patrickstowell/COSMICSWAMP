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
import plotly.express as px

import modules.iot_platform.cosmicswamp as cosmicswamp

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

app = dash.Dash(__name__)

def create_overlaid_graph(df, entity_id):
    # Create a list to store the traces (lines) for each column
    traces = []
    
    # Iterate through each column in the DataFrame
    for column_name in df.columns:
        # Create a trace for the column using a scatter plot
        if column_name in ["time_index"]: continue
        trace = go.Scatter(
            x=df.index,
            y=df[column_name],
            mode='lines',
            name=column_name
        )
        
        # Append the trace to the list of traces
        traces.append(trace)
    
    # Create a layout for the graph
    layout = go.Layout(
        title=entity_id + ' Timeseries',
        xaxis=dict(title='X-Axis'),
        yaxis=dict(title='Y-Axis')
    )
    
    # Create the graph with the traces and layout
    overlaid_graph = dcc.Graph(
        id='overlaid-graph',
        figure={'data': traces, 'layout': layout}
    )
    
    return overlaid_graph


# Orion Entity Viewer Plugin
class plugin(base_plugin):

    def __init__(self, config, app):
        super().__init__(config)        
        
    def build_widget(self, store):
        super().build_widget(store)
        
        self.service = store["Fiware-Service"]
        self.servicepath = store["Fiware-Servicepath"]
        layout = html.Div([
            self.build_plotly_list(store)
        ]
        )

        return layout
                
    def build_plotly_list(self, store):

        session = cosmicswamp.get_session_from_dict(store)
        entity_id = store["entity-selected"]
        vals = cosmicswamp.get_current_entity_from_id(session, entity_id)
        print(vals)
        keylist = ["time_index"]
        for key in vals:
            if key in ["id","type"]: continue
            if vals[key]["type"] not in ["Number","Integer"]: continue
            print(key, vals[key])
            keylist.append(str(key).lower())
        print("KEYLIST", keylist)
        df = None
        try:
            df = pd.DataFrame(data=cosmicswamp.get_series_data_for_entity(session, entity_id, attrs=keylist, limit=100000, ascending=False))
        except:
            return ""
        print("RESULT", df)

        df["date"] = pd.to_datetime(df["time_index"],unit='ms')
        # df = df.drop("time_index")
        df = df.set_index("date")

        return create_overlaid_graph(df,entity_id)
    
    
    def register_widget(self, app):
        super().register_widget(app)

        print("SDSASD")

        # Widget refresh on a local store update.
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-entity-selected","data"),
            Input("store-Fiware-Service","data"),
            Input("store-Fiware-Servicepath","data")
        )
        def refresh_custom2(search, service, path):
            store = GetStoreDefaults()
            store["entity-selected"] = search
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            print("KEYLIST CHECK")
            return self.build_widget(store)
        
    