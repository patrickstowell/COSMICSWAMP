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
                              dcc.Input(value="", id="delete-entity-name-input"),
                              html.Div("Entity Type"),
                              dcc.Input(id="delete-entity-type-input"),
                              html.Div("Entity Id"),
                              dcc.Input(id="delete-entity-id-value", value="Name Required!", disabled=True),
                ], style={"width":"1200px"}
                              ),
                dbc.ModalFooter(
                    html.Div([
                    dbc.Button(
                        "Delete", id="delete-entity-modal-delete", className="ms-auto", color="danger", n_clicks=0
                    ),
                    html.Div("", id="delete-entity-result")
                    ])
                ),
            ],
            id="delete-entity-modal",
            is_open=False,
        )
        
        layout = html.Div( [
                    html.Div(modal),
                    html.Div(id="delete-entity-dummy"),
                    html.Div( 
                        dic.DashIconify(
                            icon="line-md:plus-circle",
                            width=25,
                            color="#129"
                        ), 
                        id="delete-entity-item-icon",
                        n_clicks=0,
                        className='function-bar-item-icon'
                    )            
                    ], id="delete-entity-item", className='function-bar-item')
        
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        
        @app.callback(
            Output("delete-entity-modal","is_open"),
            Input("delete-entity-item-icon","n_clicks")
        )
        def test(n):
            print("CHECEKING N CLICKS")
            if n: return True
            raise PreventUpdate
        
        @app.callback(
            Output("delete-entity-result","children"),
            Input("delete-entity-modal-delete","n_clicks"),
            State("delete-entity-id-value","value"),
            State("store-Fiware-Service","data"),
            State("store-Fiware-Servicepath","data")
        )
        def test(n1, id, service, path):
            print("Checking for close", n1)
            if not n1: raise PreventUpdate
            
            print("Creating new ORION Entity")
            print(id, service, path)
                        
            return "Deleting!", True, False
        
            
            
                
                
                
                
            
        
        @app.callback(
            Output("delete-entity-id-value","value"),
            Output("delete-entity-modal-delete","disabled"),
            Output("delete-entity-modal-delete","color"),
            Output("delete-entity-modal-delete","children"),
            Input("delete-entity-name-input","value"),
            Input("delete-entity-type-input","value")
        )
        def entid(name, type):
            if not name: return "Name Required!", True, "danger", "Check"
            if not type: return "Type Required!", True, "danger", "Check"
            
            id = f"urn:ngsi-ld:{type}:{name}"
            id = id.replace(" ","").replace("@","")
                        
            return id, False, "success", "Create"
        
        
        
        
        