import importlib
import glob
from dash import html
import json
import os
# from factory_widgets import *
import dash_draggable
from dash import html
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from directory_tool import *
class factory_functions:

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
        if not app:
            app = self.app_default
            
        if not store:
            store = self.store_default

        # Load the layout   
        # layout_file = open(get_home() + "layouts/" + layout_name + ".json")
        # layout_config = json.load(layout_file)
        # layout_file.close()
                
        # # Loop through requested functions and add to llist
        allicons = []
        
        # # determine if side bar top shown
        # show_sidebar = 'side-bar-item-hidden'
        # if "side-bar-shown" in store and store['side-bar-shown'] == True:
        #     show_sidebar = 'side-bar-item-shown'
            
        # allicons.append(
        #         html.Div(
        #             [
        #                 html.Div( "Sidebar ", className='side-bar-item-label'),
        #                 html.Div( DashIconify(
        #                     icon="line-md:grid-3-filled",
        #                     width=25,
        #                     color="#999"
        #                 ), className='side-bar-item-icon'),
        #             ], 
        #             id="side-bar-item",
        #             className=show_sidebar
        #         )
        #     )
        
        # # If no requested, return empty div for the header.
        # if "functions" not in layout_config:
        #     functionsbar_content = html.Div(
        #         children=[
        #             html.Div(html.Div(allicons, className="function-bar-item-label"), className='function-bar')
        #         ],
        #         id="functionsbar-content"
        #     )
        #     return functionsbar_content
        
        
        for fname in glob.glob(get_assets() + "layouts/*.json"):
            temp_layout_name = fname.replace(get_assets() + "layouts/","").replace(".json","")
            layout_file = open(fname,"r")
            layout_config_in = json.load(layout_file)
            layout_file.close()
            
            # Loop over all functions and add as icons to header
            if "functions" not in layout_config_in: continue
            
            for config in layout_config_in["functions"]:
                
                print("Adding functtion", config)
                # Get requested function object
                function_name = config["id"]
                function_type = config["type"]
                
                # If function already loaded in any tab, avoid repeat build.
                if function_name in self.functionslist:
                    continue
                
                # Load the function from folder           
                print(os.getcwd())     
                function_module = importlib.import_module("assets.functions." + function_type)
                
                # Build and register
                function_object = function_module.plugin(config)
                function_object.construct_widget(store)
                function_object.register_widget(app)
                
                # Construct object and add to existing
                self.functionslist[function_name] = config
                self.functionslist[function_name]["object"] = function_object
                self.functionslist[function_name]["registered"] = True

            
        # Loop over all functions and add as icons to header
        for config_name in self.functionslist:
            config = self.functionslist[config_name]
            
            print("Adding function", config)
            # Get requested function object
            function_name = config["id"]
            function_type = config["type"]
            
            # # If function already loaded in any tab, avoid repeat build.
            # if function_type in self.functionslist:
            #     self.functionslist[function_type]["object"].construct_widget(store)
            #     continue

            # # Load the function from folder                
            # function_module = importlib.import_module("functions." + function_type)
            
            # # Build and register
            # function_object = function_module.plugin(config)
            # function_object.construct_widget(store)
            # function_object.register_widget(app)
            
            # # Construct object and add to existing
            # self.functionslist[function_type] = config
            # self.functionslist[function_type]["object"] = function_object
            # self.functionslist[function_type]["registered"] = True
            
            # Add icon to list
            allicons.append( self.functionslist[function_name]["object"].construct_widget(store) )
            
        # Return the icon list
        functionsbar_content = html.Div(
            children=[
                html.Div(allicons, className='function-bar')
            ],
            id="functionsbar-content"
        )
        return functionsbar_content

    def register(self, app):

        return
    
        
    
    