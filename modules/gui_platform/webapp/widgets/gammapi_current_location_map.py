from base_plugin import base_plugin, jst
import requests
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash import html
from dash_core_components import Interval
import time
import dash_leaflet as dl
import dash_leaflet.express as dlx
import numpy as np
from orion_handler import *
from static_store import *

# Orion Entity Chooser via Text
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        
    def get_gamma_pi(self, store, route):
        url = store["gammapi-deviceurl"] + "/" + route
        print("GAMMAPI", store, route, url)
        
        try:
            r = requests.get( url, timeout=30 )
        except requests.exceptions.ConnectionError:
            return {
                "error": "Connectitno Error"
            }
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
                
        r = self.get_gamma_pi(store, "current_positions")
        if "error" in r:
            return html.Div("Connection Error")
        
        print("POSITION RESPONSE", r)    
    
    
        markerobj = None
        alllat = []
        alllon = []
        gjslist = []
                                        
        for entry in r["positions"]:
                        
                    print(entry)
                    entity="Marker"
                    
                    if entry["lat_dir"] == "S": 
                        entry["lat"] = float(entry["lat"])*-1
                    
                    if entry["lon_dir"] == "W": 
                        entry["lon"] = float(entry["lon"])*-1
                        
                    gjs = { "type": "Point", "coordinates": [float(entry["lon"])/100.,float(entry["lat"])/100.] }
                        
                    if gjs["type"] == "Point":
                        biosfera = dlx.geojson_to_geobuf(dlx.dicts_to_geojson([dict(lat=gjs['coordinates'][0],
                                                                                    lon=gjs['coordinates'][1])]))
                        tooltip = dl.Tooltip(entity)
                        alllat.append(gjs['coordinates'][1])
                        alllon.append(gjs['coordinates'][0])
                        gjslist.append( dl.Marker(position=[gjs['coordinates'][1], gjs['coordinates'][0]], children=tooltip))

                    if gjs["type"] == "Polygon":
                        poslist = []
                        for pos in gjs['coordinates'][0]:
                            alllat.append(pos[1])
                            alllon.append(pos[0])
                            poslist.append( [pos[1],pos[0]] )

                        tooltip = dl.Tooltip(entity)
                        gjslist.append( dl.Polygon(positions=poslist, children=tooltip) )
                        
        # edit = dl.EditControl(id="edit-control",
        #                 draw=dict(polyline=False,
        #                 edit=True,
        #                 delete=False,
        #                 polygon=True,
        #                 marker=True,
        #                 circle=True,
        #                 rectangle=False,
        #                 circlemarker=False))
        
        editor = dl.EditControl(id="edit-control", 
                     draw=dict(polyline=False,
                     edit=True,
                     delete=True,
                     polygon=True,
                     marker=True,
                     circle=False,
                     rectangle=False,
                     circlemarker=False))
        
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
            ),
            editor
        ])]
        
                
        layercont = []
        layercont.append( dl.Overlay( dl.LayerGroup( gjslist ), name="Entities", checked=True ) )
        mapobjects.append(  dl.LayersControl( layercont, position="bottomright" ) )
        # mapobjects.append( dl.Overlay( dl.Marker(position=[0.0,0.0], id='central-point')))
        if len(alllat) == 0:
            alllat = [-47.853050511]
            alllon = [-21.953749685]
            
        
        
                


        m = (dl.Map(mapobjects,center=(np.mean(alllat),np.mean(alllon)), zoom=16,id='map5', 
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
                
        # Check data is valid in store add default if not
        if "entity-selected" not in store:
            store["entity-selected"] = ""
            
        entity_name = store["entity-selected"]
        
        # Construct the main widget
        layout = html.Div([
            
                html.Div(id="gammapi-current-location-map-dummy"),
                # html.Div([
                    # html.Div("Location : ", style=jst("padding-right: 10px;")),
                    # html.Div(f"[ {entity_name} ]", style=jst("padding-left: 10px; color: blue;"))
                # ], style=jst("width: 100%; padding: 5px; display: flex; flex-direction: row")),                
                html.Div(id="gammapi-current-location-map-parent", children=self.build_map(store),
                         className="map-container")
                
            ], className="map-widget")
        
        
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        