import dash_bootstrap_components as dbc
from dash import html
import dash_mantine_components as dmc
from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time

from dash.exceptions import PreventUpdate


class factory_navbar:

    def __init__(self, app, store):
        """ Conostructor

        Args:
            app (Server): Flask App Server Object
            store (dict): Default store values
        """
        self.functionslist = {}
        self.app_default = app
        self.store_default = store
        
        
    def build( self, layout_name, app = None, store = None ):
        """ Function to build navbar, right now this is static.

        Args:
            layout_config (dict):   Dict object with JSON Layout File Values.
                                    Function requests should be stored in "functions" list.
            app (Server, optional): Flask App Server Object. If None provided, uses
                                    server provided on construction. Defaults to None.
            store (dict, optional): Input store values, if none provided, defaults are used. 
                                    Defaults to None.

        Returns:
            NavBar (html.Div): HTML object containing navbar item
        """
        
        if layout_name == "":
            layout_name = "home"
        if store == None: store = self.store_default
            
        print("STORE DEFAULT", store)
        # Create the Navbar using Dash Bootstrap Components
        # navbar = dbc.NavbarSimple(
        #     children=[
        #         html.Div([
        #             html.Div("["+store["Fiware-Service"].replace("_"," ")+"]", className='client-id',style={"display":"flex","flex-grow": 1}, id='navbar-fiware-service'),
        #             html.Div(":", className='client-id',style={"display":"flex","flex-grow": 12}),
        #             html.Div("["+store["Fiware-Servicepath"].replace("_"," ")+"]", className='client-id', id='navbar-fiware-servicepath', style={"display":"flex","flex-grow": 12}),
        #             html.Div(":", className='client-id',style={"display":"flex","flex-grow": 12}),
        #             html.Div(store["geoptic-user"].replace("_"," "), className='client-id', style={"display":"flex","flex-grow": 12}),
        #             dmc.Group(
        #                 children=[
        #                     dmc.Avatar(radius="xl")
        #                 ],
        #             )
        #         ], style={"display":"flex","flex-direction": "row"})
        #     ],
        #     brand="COSMICSWAMP",  # Set the text on the left side of the Navbar
        #     brand_href="/home",  # Set the URL where the user will be sent when they click the brand we just created "Home"
        #     sticky="top",  # Stick it to the top... like Spider Man crawling on the ceiling?
        #     color="rgb(0, 100, 10)",  # Change this to change color of the navbar e.g. "primary", "secondary" etc.
        #     brand_style={"justify":"left","margin":"0"},
        #     style={"height":"70px","justify":"left"},
        #     dark=True,  # Change this to change color of text within the navbar (False for light text)
        # )
        PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"

        navbar = dbc.Navbar(
            dbc.Container(
                [
                    dbc.Col(
                        html.A(
                            # Use row and col to control vertical alignment of logo / brand
                            dbc.Row(
                                [
                                    dbc.Col(html.Img(src=PLOTLY_LOGO, height="40px")),
                                    dbc.Col(dbc.NavbarBrand("COSMICSWAMP", className="ms-2")),
                                ],
                                align="center",
                                className="g-0",
                            ),
                            href="/home",
                            style={"textDecoration": "none"},
                        ), width=3 
                    ),
                    dbc.Col("-", width=7),
                    dbc.Col(
                        html.A(
                            # Use row and col to control vertical alignment of logo / brand
                            dbc.Row(
                                [
                                    dbc.Col(store["Fiware-Service"], id='navbar-fiware-service',className="ms-2"),
                                    dbc.Col(store["Fiware-Servicepath"], id='navbar-fiware-servicepath',className="ms-2"),
                                    dbc.Col(store["geoptic-user"].replace("_"," "), id='navbar-user', className="ms-2")
                                ],
                                align="right",
                                className="g-0",
                            ),
                            href="/service_editor",
                            style={"textDecoration": "none"},
                        ), width=4
                    )
                ]
            ),
            color="dark",
            dark=True,
            style={"height":"70px"}
        )
        
        # Return the object as dash wrapped
        navbar_content = html.Div(
            children=[
                navbar
            ]
        )
        return navbar_content
    
    def register(self, app):

        @app.callback( 
                    Output("navbar-fiware-service","children"),
                    Input("store-Fiware-Service","data")
                )
        def set_fiwareservice(path):
            if not path: raise PreventUpdate  
            return "[" + path + "]"
        
        @app.callback( 
                    Output("navbar-fiware-servicepath","children"),
                    Input("store-Fiware-Servicepath","data")
                )
        def set_fiwareservice(path):
            if not path: raise PreventUpdate  
            return "[" + path + "]"
        

        return