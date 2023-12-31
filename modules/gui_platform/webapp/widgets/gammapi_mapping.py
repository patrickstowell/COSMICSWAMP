from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time
import dash_leaflet as dl
import numpy as np
from orion_handler import *
from static_store import *

def dmconv(x):
    south = False
    
    if x<0:
        south = True
        x = math.abs(x)
        
    degrees = int(x) // 100
    minutes = x - 100*degrees
    
    x = degrees + minutes/60
    if south:
        x = -x
    return x

# Orion Entity Chooser via Text
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
        
    def build_map(self, store):
        """ Map Generatr

        Args:
            store (dict): Map storage object
        """
        # Query ORION for entity current location
        # Get all entities in current path
                
        # Setup ORION Call
        gpsdata = self.get_gamma_pi(store, "gps")
                
        markerobj = None
        alllat = []
        alllon = []
        gjslist = []
        for key in gpsdata:
            print(key)
        poslist = []
        for entry in gpsdata["0"]["parent"]:
            entry["lat"] = dmconv(float(entry["lat"]))
            entry["lon"] = dmconv(float(entry["lon"]))
            
            if entry["lon_dir"] == "W": entry["lon"] *= -1
            if entry["lat_dir"] == "S": entry["lat"] *= -1

            alllat.append(entry["lat"])
            alllon.append(entry["lon"])
            poslist.append( [entry["lat"],entry["lon"]] )
            
        gjslist.append( dl.Polyline(positions=poslist, children="Positions All") )
                
        
        mapobjects = [
            dl.TileLayer(),
            dl.FeatureGroup([
            dl.LayersControl(
            [
                dl.Overlay(dl.TileLayer(url="http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}"),name="Satellite", checked=False),
                dl.Overlay(dl.TileLayer(url="http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}"),name="Terrain", checked=False),
                dl.Overlay(dl.TileLayer(url="http://mt0.google.com/vt/lyrs=t&hl=en&x={x}&y={y}&z={z}"),name="Terrain Only", checked=False)
            ],
            position="topright"
            )
        ])]
        
                
        layercont = []
        layercont.append( dl.Overlay( dl.LayerGroup( gjslist ), name="Entities", checked=True ) )
        mapobjects.append(  dl.LayersControl( layercont, position="bottomright" ) )
        # mapobjects.append( dl.Overlay( dl.Marker(position=[0.0,0.0], id='central-point')))
        if len(alllat) == 0:
            alllat = [-47.853050511]
            alllon = [-21.953749685]
            
        m = (dl.Map(mapobjects,center=(np.mean(alllat),np.mean(alllon)), zoom=16,id='gammapi-map', 
        style={'display':'flex', 'flex-direction': 'row', 'flex-grow':'1', 'min-width': "365px", 'max-width': "1200px",'height': '375px'}))
        # dl.SearchControl(
        #     position="topleft",
        #     url='https://nominatim.openstreetmap.org/search?format=json&q={s}',
        #     zoom=14,
        #     marker=marker
        #     )
        
        mapobj = html.Div(m)
        
        return mapobj
        
        
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
            
                html.Div(id="gammapi-location-map-dummy"),                
                html.Div(id="gammapi-location-map-parent", children=self.build_map(store),
                        className="map-container")
                
            ], className="map-widget")
        
        
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        