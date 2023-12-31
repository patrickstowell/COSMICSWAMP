import json
from factory_widgets import *
import dash_draggable
from dash import html
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from factory_functions import *
from factory_layouts import create_dynamic_widget
from layout_helper import *
from directory_tool import *

def jst(data):
    style = {}
    for keys in data.split(";"):
        vals = keys.split(":")
        if len(vals) <= 1: continue
        style[ vals[0].strip() ] = vals[1].strip()
    return style

class factory_layouts:
    def __init__(self, app, store):        
        self.id = ""
        self.app_default = app
        self.store_default = store
        self.layouts = {}
        self.widgetlist = {}

        
    def build( self, layout_name, app, store ):
        
        if layout_name == "":
            layout_name = "home"

        # if layout_name == "loading":
            # return html.Div("")
            
        # Check for Defaults
        if not app:
            app = self.app_default
            
        if not store:
            store = self.store_default       
            
        if layout_name in self.layouts:
            self.layouts[layout_name]
            return self.layouts[layout_name]

        # On first build we generate all layouts
        
        self.widgetpositions = []
        for fname in glob.glob(get_home() + "layouts/*.json"):

            temp_layout_name = fname.replace(get_home() + "layouts/","").replace(".json","")

            # Don't rebuild all if we already built
            if layout_name in self.layouts and layout_name != temp_layout_name:
                continue
                    
            layout_file = open(fname,"r")
            layout_json = json.load(layout_file)
            layout_file.close()
            self.widgetdivs = []

            # Return dynamic widgets
            for widget in layout_json["widgets"]:
                if widget["id"] not in self.widgetlist:
                    self.widgetlist[widget["id"]] = ( create_dynamic_widget( widget, app, store ) )
                    self.widgetlist[widget["id"]].register_widget(app)

                self.widgetdivs.append( self.widgetlist[widget["id"]].construct_widget(store))
                
                w = 5
                h = 3 
                x = 0
                y = 0
                static = False
                
                if "w" in widget: w = widget["w"]
                if "h" in widget: h = widget["h"]
                if "x" in widget: x = widget["x"]
                if "y" in widget: y = widget["y"]
                if "static" in widget: static = widget["static"]
                
                self.widgetpositions.append( {
                    "w": w,
                    "h": h,
                    "x": x,
                    "y": y,
                    "i": widget["id"] + "-box",
                    "moved": False,
                    "static": static
                })
                
            # Add all widgets to the grid
            if layout_json["type"] == "GridLayout":
                layout = html.Div([
                    # html.Div(children=self.widgetdivs)
                    # CustomGridLayout(
                    #     id=f"{self.id}-draggable",
                    #     children=self.widgetdivs,
                    #     layout=self.widgetpositions,
                    #     height=10)
                    dash_draggable.GridLayout(
                        id=f"{self.id}-draggable",
                        children=self.widgetdivs,
                        layout=self.widgetpositions)
                    ])
                
                
            elif layout_json["type"] == "Single":
                layout = html.Div(
                    self.widgetdivs
                , className="single-dash", style={"display":"flex", "flex-grow": 12})
                
            else:
                layout = html.Div("")
            
            self.layouts[temp_layout_name] = layout
        
        
        return self.layouts[layout_name]

    def register(self, app, store):
        for fname in glob.glob(get_home() + "layouts/*.json"):

            temp_layout_name = fname.replace(get_home() + "layouts/","").replace(".json","")
                    
            layout_file = open(fname,"r")
            layout_json = json.load(layout_file)
            layout_file.close()

            # Return dynamic widgets
            for widget in layout_json["widgets"]:
                if widget["id"] not in self.widgetlist:
                    self.widgetlist[widget["id"]] = ( create_dynamic_widget( widget, app, store ) )
                    self.widgetlist[widget["id"]].register_widget(app)

        return

        