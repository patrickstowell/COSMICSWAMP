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
import modules.iot_platform.cosmicswamp as cosmicswamp
import dependencies.geojson_utils as geojson_utils
import colorsys

def value_to_color_old(value):
    # Calculate the red and blue components
    red = int(255 * (1 - value))
    blue = int(255 * value)
    # Return the RGB color as a string in the format "rgb(r, 0, b)"
    return f'rgb({red}, 0, {blue})'

def dummy_marker():
    return dl.Marker(position=[12,54], children="")

def value_to_color(value):
    # Convert the value to a hue value in the range [0, 1]
    hue = value
    # Get the RGB color corresponding to the hue value
    rgb_color = colorsys.hsv_to_rgb(hue, 1, 1)
    # Scale the RGB values from [0, 1] to [0, 255] and round them
    scaled_rgb = [round(val * 255) for val in rgb_color]
    # Return the RGB color as a string in the format "rgb(r, g, b)"
    return f'rgb({scaled_rgb[0]}, {scaled_rgb[1]}, {scaled_rgb[2]})'

# Orion Entity Chooser via Text
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        self.delayed_register_done = False 
        self.app = app
        
    def location_to_marker(self, gjs, entity, highlight, scale):

        tooltip = dl.Tooltip(entity)
        if gjs["type"] == "Point":
            gjs = geojson_utils.circle_around_point(gjs,radius=10)

        print("TYPE",gjs)
        if gjs["type"] == "Point":
            if highlight: return dl.Marker(position=[gjs['coordinates'][1], gjs['coordinates'][0]], children=tooltip)
            else: return dl.Marker(position=[gjs['coordinates'][1], gjs['coordinates'][0]], children=tooltip, opacity=0.1, style={"color":value_to_color(scale)})

        if gjs["type"] == "Polygon":
            poslist = []
            for pos in gjs['coordinates'][0]:
                poslist.append( [pos[1],pos[0]] )

            print(value_to_color(scale), scale)
            if highlight: return dl.Polygon(positions=poslist, children=tooltip)
            else: return dl.Polygon(positions=poslist, children=tooltip, fillOpacity=0.1, opacity=1.0, color=value_to_color(scale), fillColor=value_to_color(scale)) 

    def get_selected_marker(self, store):

        session = cosmicswamp.get_session_from_dict(store)
        entity_id = store["entity-selected"]
        entity = entity_id

        try:
            entity_vals = cosmicswamp.get_current_entity_from_id(session, entity_id)
            if not entity_vals:
                return dl.Marker(position=[12,54], children="")
            
            if "location" not in entity_vals:
                return dl.Marker(position=[12,54], children="")
            
            marker = self.location_to_marker( entity_vals["location"]["value"], entity_id, True, 1.0)

            return marker
        except:
            return dummy_marker()
    
    def get_all_marker(self, store):

        try:
                
            session = cosmicswamp.get_session_from_dict(store)
            entity_id = store["entity-selected"]
            entity = entity_id

            print("RESTRICTED TYPE", self.restrict_types)
            if self.restrict_types != None:
                all_entities = cosmicswamp.get_all_current_entities_of_type(session, self.restrict_types)
            else:
                all_entities = cosmicswamp.get_all_current_entity_ids(session)
            valid_entities = []
            for e in all_entities:
                if self.restrict_types:
                    if e["type"] != self.restrict_types: continue
                else:
                    if "entity-search" in store and store["entity-search"] != "" and not store["entity-search"] in e["id"]: continue
                    if "type-search" in store and store["type-search"] != "" and not store["type-search"] in e["type"]: continue

                valid_entities.append(cosmicswamp.get_current_entity_from_id(session,e["id"]))

            if not valid_entities or len(valid_entities) == 0:
                return dl.Marker(position=[12,54], children="")
            
            smlist = []
            for entity_vals in valid_entities:
                if "soilmoisturecalibrated0" in entity_vals:
                    smlist.append(entity_vals["soilmoisturecalibrated0"]["value"])
            
            print(smlist)
            markerlist = []
            for entity_vals in valid_entities:
                entity_id = entity_vals["id"]
                if "location" not in entity_vals: continue      
                scale = 1.0 
                if "soilmoisturecalibrated0" in entity_vals:
                    scale = (entity_vals["soilmoisturecalibrated0"]["value"]-0.15)/(0.25-0.15)
                    if scale > 1.0: scale = 1.0
                    if scale < 0.0: scale = 0.0
                marker = self.location_to_marker( entity_vals["location"]["value"], entity_id, False, scale)
                markerlist.append(marker)

            if len(markerlist) == 0:
                return dummy_marker()
        
        
            return markerlist
        except:
            return [dummy_marker()]



    def build_map(self, store):
        
        tiles = dl.TileLayer()

        editor = dl.EditControl(id="edit-control", 
                    draw=dict(polyline=False,
                    edit=True,
                    delete=True,
                    polygon=True,
                    marker=True,
                    circle=False,
                    rectangle=False,
                    circlemarker=False))
        
        layers = dl.LayersControl(
            [
                dl.Overlay(dl.TileLayer(url="http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}"),name="Satellite", checked=False),
                dl.Overlay(dl.TileLayer(url="http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}"),name="Terrain", checked=False),
                dl.Overlay(dl.TileLayer(url="http://mt0.google.com/vt/lyrs=t&hl=en&x={x}&y={y}&z={z}"),name="Terrain Only", checked=False)
            ],
            position="topright"
            )
        
        mapobjects = [
            tiles,
            dl.FeatureGroup([layers])
        ]
    
        mapobjects.append( dl.FeatureGroup([self.get_selected_marker(store)], id=self.id + "-selected-marker") )
        mapobjects.append( dl.FeatureGroup(self.get_all_marker(store), id=self.id + "-all-marker") )


        # print("ALLLAT", alllat, alllon)
        # if len(alllat) == 0:
        alllon = [-12.169397]
        alllat = [-45.519485]
    
        m = (dl.Map(mapobjects,center=(np.mean(alllon),np.mean(alllat)), zoom=13,id='map2', 
        style={'display':'flex', 'flex-direction': 'row', 'flex-grow':'1', 'min-width': "365px", 'max-width': "1200px",'height': '525px', 'margin-left':'10px', 'margin-right':'10px'}))
        
        mapobj = html.Div(m)
        
        return mapobj, (np.mean(alllon),np.mean(alllat))
        
        
    def build_widget(self, store):
        super().build_widget(store)
                
        # Check data is valid in store add default if not
        if "entity-selected" not in store:
            store["entity-selected"] = ""
            
        entity_name = store["entity-selected"]
        
        mapobj, mapcen = self.build_map(store)
        # Construct the main widget
        layout = html.Div([
            
                html.Div(id="orion-location-view-map-dummy"),
                html.Div(id="orion-location-view-map-parent", children=mapobj,
                        className="map-container")
                
            ], className="map-widget")
        
        if (not self.delayed_register_done):
            self.delayed_register()
            self.delayed_register_done = True
        return layout
                
    def register_widget(self, app):
        super().register_widget(app)
        self.app = app
        
    def delayed_register(self):
        app = self.app
        print("DELAYING REGISTRATION")
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-entity-search","data"),
            Input("store-type-search","data"),
            State("store-Fiware-Service","data"),
            State("store-Fiware-Servicepath","data")
        )
        def refresh_custom(entity, types, service, path):
            if entity == None: raise PreventUpdate
            store = GetStoreDefaults()
            store["entity-search"] = entity
            store["type-search"] = types
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            return self.build_widget(store)
        
        @app.callback( 
            Output(self.id + "-selected-marker", "children"),
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
            return [self.get_selected_marker(store)]
        
        # @app.callback(
        #     Output("orion-location-view-map-dummy", "children"),
        #     Input("edit-control", "geojson"),
        #     State("store-entity-selected","data"),
        #     State("store-Fiware-Service","data"),
        #     State("store-Fiware-Servicepath","data")
        #     )
        # def update_entity_location(x, entity, service, path):
        #     """ Uploads a new geojson entity location based on map input

        #     Args:
        #         x (dict): callback passed geojson list

        #     Returns:
        #         dash data table: Updates attribute table contents.
        #     """
        #     # Update Checks
        #     print("EDIT CONTRTOL TRIGGERED")
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
        #     data={"location":{"value":x["features"][-1]["geometry"]}}
            
        #     print("ENTITY LOCATION FEATURE")
        #     ORION.service = service
        #     ORION.servicepath = path
        #     ORION.update_entity_attrs(entity, data)
            
        #     return ""
