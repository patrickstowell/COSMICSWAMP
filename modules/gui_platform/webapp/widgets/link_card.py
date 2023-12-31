import requests
import time
import importlib
import glob
import json

from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_draggable
import dash_bootstrap_components as dbc
from dash_core_components import Interval
from dash_iconify import DashIconify

from factory_widgets import *
from base_plugin import base_plugin, jst
#
# Orion Path Chooser
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)

    def build_widget(self, store):
        super().build_widget(store)
                        
        # Construct the main widget
        layout = html.Div(
            dcc.Link(
                    children=html.Div(
                        [
                            html.Div( DashIconify(
                                icon=self.icon,
                                width=self.icon_size,
                                color=self.icon_color
                            ), className=self.className + '-icon'),
                            html.Div( self.label, className=self.className + '-label')
                        ], 
                        className=self.className
                    ), 
                    href=self.url
                )
        )
        
        return layout

    def register_widget(self, app):
        super().register_widget(app)

            
        
        