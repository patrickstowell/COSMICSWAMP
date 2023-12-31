import os
from glob import glob
from pathlib import Path
import sys

current_file = __file__
current_path = __file__.strip(__file__.split("/")[-1])
resources_folder = current_path + "/assets/"

sys.path.append(current_path)

import dash
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, html

from dash.dependencies import Input, Output
from dash import Dash, html, dcc
import threading
import plotly.express as px
import pandas as pd
import flask
import os
import dash_draggable

from dash import Dash, html
from flask import Flask
from flask.helpers import get_root_path

from factory_widgets import *
from factory_layouts import *
from dash_tools import *
from factory_sidebar import *
# from factory_functions import *
from factory_navbar import *
from static_store import *

################################
# App Definition
################################
server = Flask(__name__)
app = DashProxy(__name__, 
                transforms=[MultiplexerTransform()], 
                suppress_callback_exceptions=True, 
                server=server,
                prevent_initial_callbacks=True)
        
#################################
# Dynamic Layout Tools
#################################
# store, store_header = DynamicStore(app, "local_storage_default.json")
store_default = GetStoreDefaults()
store_header  = RegisterStore()

layout_builder      = factory_layouts(app,   store_default)
navbar_builder      = factory_navbar(app,    store_default)
sidebar_builder     = factory_sidebar(app,   store_default)
# functionbar_builder = factory_functions(app, store_default)

def display_dashboard(pathname, store=None):
    layout = layout_builder.build(pathname.strip("/"), app, store=store)  
    return layout

def display_navbar(pathname, store=None):
    layout = navbar_builder.build(pathname.strip("/"), app, store=store)   
    return layout

def display_sidebar(pathname, store=None):
    layout = sidebar_builder.build(pathname.strip("/"), app, store=store)  
    return layout

# def display_functionbar(pathname, store=None):
    # layout = functionbar_builder.build(pathname.strip("/"), app, store=store)  
    # return layout

#################################
# Default Layout
#################################
app.layout = html.Div(children=[
    
    html.Div(id="page-updater"),
    store_header, 
    dcc.Location(id='url'),
    
    html.Div( display_navbar("/home"), id="navbar-content", className='navbar-content'),
    # html.Div( display_functionbar("/home"), id="functionbar-content", className='functionbar-content'),
    html.Div([
        html.Div(display_sidebar("/home"), id='sidebar-content', className='sidebar-content'),
        html.Div(display_dashboard("/home"), id='dashboard-content', className='dashboard-content')
        ], className="sidebar-dashboard-content"
    )
    
    ], className='main-body'
)

#################################
# Register callbacks for layout
#################################
layout_builder.register(app, store_default)
navbar_builder.register(app)
sidebar_builder.register(app)
# functionbar_builder.register(app)

#################################
# Define main page callback
#################################
@app.callback(
        Output('navbar-content', 'children'),
        Input('url', 'pathname'),
        GetStoreState()
)
def update_navbar(pathname, *storestate):
    print("Updated PathName", pathname)
    store = FillStoreState(storestate)
    return display_navbar(pathname, store)

# @app.callback(
#         Output('functionbar-content', 'children'),
#         Input('url', 'pathname'),
#         GetStoreState()
# )
# def update_functionbar(pathname, *storestate):
#     store = FillStoreState(storestate)
#     return display_functionbar(pathname, store)

@app.callback(
        Output('sidebar-content', 'children'),
        Input('url', 'pathname'),
        GetStoreState()
        )
def update_sidebar(pathname, *storestate):
    store = FillStoreState(storestate)
    return display_sidebar(pathname, store)

@app.callback(
        Output('dashboard-content', 'children'),
        Input('url', 'pathname'),
        GetStoreState()
)
def update_dashboard(pathname,*storestate):
    print("Updated PathName", pathname)
    store = FillStoreState(storestate)
    return display_dashboard(pathname, store)

# Links
@app.callback(Output('store-field-selected', 'data'),
            Input('store-entity-selected', 'data'))
def select_field(path):
    if not path or not "Field" in path: raise PreventUpdate
    return path

@app.callback(Output('store-probe-selected', 'data'),
            Input('store-entity-selected', 'data'))
def select_probe(path):
    if not path or not "Probe" in path: raise PreventUpdate
    return path

@app.callback(Output('store-neutronprobe-selected', 'data'),
            Input('store-entity-selected', 'data'))
def select_probe(path):
    if not path or not "NeutronProbe" in path: raise PreventUpdate
    return path

@app.callback(Output('store-soildepthprobe-selected', 'data'),
            Input('store-entity-selected', 'data'))
def select_probe(path):
    if not path or not "SoilDepthProbe" in path: raise PreventUpdate
    return path

@app.callback(Output('store-agronomy-selected', 'data'),
            Input('store-entity-selected', 'data'))
def select_probe(path):
    if not path or not "Agronomy" in path: raise PreventUpdate
    print("AGRONOMY", path)
    return path


def start_server():
    app.run_server(debug=False, port='5081')

if __name__ == '__main__':
    app.run_server(debug=True, port='5081') 