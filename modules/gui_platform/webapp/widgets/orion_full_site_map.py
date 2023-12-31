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
        
    def build_map(self, store):
        """ Map Generatr

        Args:
            store (dict): Map storage object
        """
        # Query ORION for entity current location
        # Get all entities in current path
                
        # Setup ORION Call
        ORION.service = store["Fiware-Service"]
        ORION.servicepath = store["Fiware-Servicepath"]
        print("MAP", ORION.service, ORION.servicepath)
        vals = ORION.get_entities()
        entity = store["entity-selected"]
        print("Building full sie mp")
        print("SIETE", ORION.servicepath)
        markerobj = None
        alllat = []
        alllon = []
        gjslist = {}
        
        typecolors = {
        "Crop":"Black",
        "Agronomy":"Black",
        "ManagementZone":"White",
        "WeatherObserved":"Red",
        "WeatherForecast":"Pink",
        "Farm":"Blue",
        "Field":"Green",
        "Building":"Gray",
        "Road":"Black",
        "Trees":"Green",
        "Soil":"White",
        "NeutronProbe":"Red",
        "NeutronProbeCalibrated":"Pink",
        "SoilDepthProbe":"Red",
        "SoilDepthProbeCalibrated":"Red",
        "PivotArm" : "Red"
        }
        print("MAP", vals)
        if "error" in vals: 
            print("SITE ERROORSES")
            return html.Div("ERROR")
        
        print("MAP ENTITYS", vals)             
        for entity in vals:
                     
                id = entity["id"]
                types = entity["type"]
                   
                if "location" in entity:
                    
                    if "value" in entity["location"]:
                        gjs = entity["location"]["value"]
                    else:
                        gjs = entity["location"]
                        
                    if gjs["type"] == "Point":
                        #biosfera = dlx.geojson_to_geobuf(dlx.dicts_to_geojson([dict(lat=gjs['coordinates'][0],
                        #                                                            lon=gjs['coordinates'][1])]))
                        tooltip = dl.Tooltip(id)
                        alllat.append(gjs['coordinates'][1])
                        alllon.append(gjs['coordinates'][0])
                        if types not in gjslist: gjslist[types] = []
                        gjslist[types].append( dl.Marker(position=[gjs['coordinates'][1], gjs['coordinates'][0]], children=tooltip))

                    if gjs["type"] == "Polygon":
                        poslist = []
                        for pos in gjs['coordinates'][0]:
                            alllat.append(pos[1])
                            alllon.append(pos[0])
                            poslist.append( [pos[1],pos[0]] )

                        tooltip = dl.Tooltip(id)
                        if types not in gjslist: gjslist[types] = []
                        gjslist[types].append( dl.Polygon(positions=poslist, color=typecolors[types], children=tooltip) )
                        
        # edit = dl.EditControl(id="edit-control",
        #                 draw=dict(polyline=False,
        #                 edit=True,
        #                 delete=False,
        #                 polygon=True,
        #                 marker=True,
        #                 circle=True,
        #                 rectangle=False,
        #                 circlemarker=False))
        
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
        
        print("GJSLIST", gjslist)
        layercont = []
        for types in gjslist:
            layercont.append( dl.Overlay( dl.LayerGroup( gjslist[types] ), name=types, checked=True ) )
        mapobjects.append(  dl.LayersControl( layercont, position="bottomright" ) )
        if len(alllat) == 0:
            alllat = [-47.853050511]
            alllon = [-21.953749685]
            
        mapobj = html.Div(dl.Map(mapobjects,center=(np.mean(alllat),np.mean(alllon)), zoom=16,id='fullsitemap',
        style={'display':'flex', 'flex-direction': 'row', 'flex-grow':'12', 'min-width': "1400px", 'max-width': "1400px",'height': '600px'})
        )
        
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
            
                html.Div(id="orion-full-site-map-dummy"),
                # html.Div([
                    # html.Div("Location : ", style=jst("padding-right: 10px;")),
                    # html.Div(f"[ {entity_name} ]", style=jst("padding-left: 10px; color: blue;"))
                # ], style=jst("width: 100%; padding: 5px; display: flex; flex-direction: row")),
                                
                html.Div(id="orion-full-site-map-parent", children=self.build_map(store),
                         className="map-container")
                
            ], className="map-widget")
        
        print("FULL SITE MAP LOADING")
        return layout
                
    def register_widget(self, app):
        """ Function to register callbacks in the widget.

        Args:
            app (Server): Flask server for web application.
            
        """
        super().register_widget(app)
        
        # Widget refresh on a local store update.
        # @app.callback( 
        #     Output(f"{self.id}-box", "children"),
        # )
        # def refresh_custom(store_changes):
            
        #     return self.build_widget(store)
        
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-entity-selected","data"),
            State("store-Fiware-Service","data"),
            State("store-Fiware-Servicepath","data")
        )
        def refresh_custom(entity, service, path):
            if entity == None: raise PreventUpdate
            store = GetStoreDefaults()
            store["entity-selected"] = entity
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            return self.build_widget(store)
            # raise PreventUpdate
        
        # @app.callback(
        #     Output("data-attribute-table-parent", "children"),
        #     Input("edit-control", "geojson")
        #     )
        # def update_entity_location(x):
        #     """ Uploads a new geojson entity location based on map input

        #     Args:
        #         x (dict): callback passed geojson list

        #     Returns:
        #         dash data table: Updates attribute table contents.
        #     """
        #     # Update Checks
        #     if not x:
        #         raise PreventUpdate
        #     if isinstance(x["features"],bool):
        #         raise PreventUpdate 
        #     if not x["features"]: 
        #         raise PreventUpdate
        #     if len(x["features"]) == 0:
        #         raise PreventUpdate
            
        #     # Get the last feature produced
        #     feature = x["features"][-1]
            
        #     # Construct the Orion Interface
        #     entity = self.current_entity
        #     data={"location":{"value":x["features"][-1]["geometry"]}}
        #     ORION.update_entity_attrs(self.current_entity, data)
            
        #     return self.build_atttribute_table(self.current_entity)
