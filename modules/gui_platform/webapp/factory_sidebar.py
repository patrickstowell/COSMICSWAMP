import importlib
import glob
from dash import html
import json
from factory_widgets import *
import dash_draggable
from dash import html
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from directory_tool import *


class factory_sidebar:

    def __init__(self, app, store):
        """ Conostructor

        Args:
            app (Server): Flask App Server Object
            store (dict): Default store values
        """
        self.sidebarlist = {}
        self.app_default = app
        self.store_default = store
        
    
    def build( self, layout_name, app = None, store = None ):
        """ Main Function Header Build

        Args:
            layout_config (dict):   Dict object with JSON Layout File Values.
                                    Function requests should be stored in "functions" list.
            app (Server, optional): Flask App Server Object. If None provided, uses
                                    server provided on construction. Defaults to None.
            store (dict, optional): Input store values, if none provided, defaults are used. 
                                    Defaults to None.

        Returns:
            Header (html.Div): HTML object containing function icons.
        """
        
        if layout_name == "":
            layout_name = "home"

        # Check for Defaults
        if not app: app = self.app_default
        if not store: store = self.store_default
                    
        # Load the layout           
        sidebar_entries = []
        orderlist = []
        idlist = []
                
        for fname in glob.glob(get_home() + "/layouts/*.json"):

            ffile = open(fname,"r")
            fjson = json.load(ffile)
            ffile.close()
            
            idv = fname.replace(".json","").replace(get_home() + "/layouts/","")
            print(idv)
            sidebarsel = 'side-bar-item'
            if layout_name in fname: 
                sidebarsel = 'side-bar-item-selected'
            
            ordering = fjson["order"]
            while ordering in orderlist:
                ordering += 1
            orderlist.append(ordering)
            idlist.append(idv)
            
            sidebar_entries.append(
                dcc.Link(
                    children=html.Div(
                        [
                            html.Div( fjson["title"], className='side-bar-item-label'),
                            html.Div( DashIconify(
                                icon=fjson["icon"],
                                width=25,
                                color="#129"
                            ), className='side-bar-item-icon'),
                        ], 
                        className=sidebarsel
                    ), 
                    href="/" + idv
                )
            )

        print("LEN SIDEBAR", sidebar_entries)
            
        # keep in a dict the index for each value from Ref
        # sort by the index value from Ref for each number from Input 
        sidebar_entries = [i for _,i in sorted(zip(orderlist, sidebar_entries))]
        idlist = [i for _,i in sorted(zip(orderlist, idlist))]
        orderlist = [i for _,i in sorted(zip(orderlist,orderlist))]

        sidebar_content = html.Div(
                sidebar_entries,
                id='side-bar',
            className='side-bar')
        
        return sidebar_content

    def register(self, app):
        return