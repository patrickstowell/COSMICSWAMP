from base_function import base_function, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import dash_iconify as dic
import json
import time

# Orion Entity Chooser via Text
class plugin(base_function):
    def __init__(self, config):
        super().__init__(config)
        
    def build_widget(self, store):
        """ Main Widget Construction, called on page updates.

        Args:
            store (dict): JSON Data Store Input

        Returns:
            html Layout Object: All outputs should be wrapped in a html.Div
        """
        super().build_widget(store)
                
        
        modal = dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Create New Entity")),
                dbc.ModalBody([
                            html.Div("Entity Name"),
                            dcc.Input(value="", id="new-entity-name-input"),
                            html.Div("Entity Type"),
                            dcc.Input(id="new-entity-type-input"),
                            html.Div("Entity Id"),
                            dcc.Input(id="new-entity-id-value", value="Name Required!", disabled=True),
                            html.Div("Entity Attributes [JSON]"),
                            dcc.Textarea(id="new-entity-attribute-input", style={"width":"450px"})
                ], style={"width":"1200px"}
                ),
                dbc.ModalFooter(
                    html.Div([
                    dbc.Button(
                        "Check", id="new-entity-modal-create", className="ms-auto", color="danger", n_clicks=0
                    ),
                    html.Div("", id="new-entity-result")
                    ])
                ),
            ],
            id="new-entity-modal",
            is_open=False,
        )
        
        layout = html.Div( [
                    html.Div(modal),
                    html.Div(id="new-entity-dummy"),
                    html.Div( 
                        dic.DashIconify(
                            icon="line-md:plus-circle",
                            width=25,
                            color="#129"
                        ), 
                        id="new-entity-item-icon",
                        n_clicks=0,
                        className='function-bar-item-icon'
                    )            
                    ], id="new-entity-item", className='function-bar-item')
        
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        
        @app.callback(
            Output("new-entity-modal","is_open"),
            Input("new-entity-item-icon","n_clicks")
        )
        def test(n):
            if n: return True
            raise PreventUpdate
        
        @app.callback(
            Output("new-entity-result","children"),
            Input("new-entity-modal-create","n_clicks"),
            State("new-entity-id-value","value"),
            State("new-entity-attribute-input","value"),
            State("store-Fiware-Service","data"),
            State("store-Fiware-Servicepath","data")
        )
        def test(n1, id, attrs, service, path):
            print("Checking for close", n1)
            if not n1: raise PreventUpdate
            
            print("Creating new ORION Entity")
            print(id, attrs, service, path)
            
            try:
                jsondata = json.loads(attrs)
            except:
                return "Failed to parse attributes!"
            
            
            return "Oh no!", True, False
        
        @app.callback(
            Output("new-entity-result","children"),
            Input("new-entity-modal-check","n_clicks"),
            State("new-entity-id-value","value"),
            State("new-entity-attribute-input","value"),
        )
        def test(n1, id, attrs):
            print("Checking for close", n1)
            if not n1: raise PreventUpdate
            
            print("Checeking new ORION Entity")
            print(id, attrs)
            
            try:
                jsondata = json.loads(attrs)
            except:
                return "Failed to parse attributes!"
            
            
            return "NGSI Valid"
            
            
                
                
                
                
            
        
        @app.callback(
            Output("new-entity-id-value","value"),
            Output("new-entity-modal-create","disabled"),
            Output("new-entity-modal-create","color"),
            Output("new-entity-modal-create","children"),
            Input("new-entity-name-input","value"),
            Input("new-entity-type-input","value"),
            Input("new-entity-attribute-input","value")
        )
        def entid(name, type, attrs):
            if not name: return "Name Required!", True, "danger", "Check"
            if not type: return "Type Required!", True, "danger", "Check"
            
            id = f"urn:ngsi-ld:{type}:{name}"
            id = id.replace(" ","").replace("@","")
            
            try:
                jsondata = json.loads(attrs)
            except:
                return id, False, "danger", "Check"
            
            return id, False, "success", "Create"
        
        
        
        
        