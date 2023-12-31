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


# Orion Entity Chooser via Text
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        
    def build_map(self, store):
        session = cosmicswamp.get_session_from_dict(store)
        entity_id = store["entity-selected"]
        vals = cosmicswamp.get_current_entity_from_id(session, entity_id)
        entity = entity_id


        all_entities = cosmicswamp.get_all_current_entity_ids(session, limit=1000)
        valid_entities = []
        for e in all_entities:
            if "entity-search" in store and store["entity-search"] != "" and not store["entity-search"] in e["id"]: continue
            if "type-search" in store and store["type-search"] != "" and not store["type-search"] in e["type"]: continue
            valid_entities.append(cosmicswamp.get_current_entity_from_id(session,e["id"]))

        markerobj = None
        alllat = []
        alllon = []
        gjslist = []
                                        
        for vals in valid_entities:

            opacity_value = 0.1
            interactive_value = False
            if vals["id"] == entity:
                opacity_value = 1.0
            if "location" in vals:

                gjs = vals["location"]["value"]
                    
                if gjs["type"] == "Point":
                    tooltip = dl.Tooltip(entity)
                    alllat.append(gjs['coordinates'][1])
                    alllon.append(gjs['coordinates'][0])
                    gjslist.append( dl.Marker(position=[gjs['coordinates'][1], gjs['coordinates'][0]], children=tooltip, opacity=opacity_value, interactive=interactive_value))

                if gjs["type"] == "Polygon":
                    poslist = []
                    for pos in gjs['coordinates'][0]:
                        alllat.append(pos[1])
                        alllon.append(pos[0])
                        poslist.append( [pos[1],pos[0]] )

                    tooltip = dl.Tooltip(entity)
                    gjslist.append( dl.Polygon(positions=poslist, children=tooltip, fillOpacity=opacity_value, interactive=interactive_value) )

        
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

        print("ALLLAT", alllat, alllon)
        # if len(alllat) == 0:
        alllon = [-12.169397]
        alllat = [-45.519485]
    
        # search = dl.SearchControl(
        #     position="topleft",
        #     url='https://nominatim.openstreetmap.org/search?format=json&q={s}',
        #     zoom=14
        #     )
        m = (dl.Map(mapobjects,center=(np.mean(alllon),np.mean(alllat)), zoom=16,id='map2', 
        style={'display':'flex', 'flex-direction': 'row', 'flex-grow':'1', 'min-width': "365px", 'max-width': "1200px",'height': '450px'}))
        
        
        
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
        
        
        return layout
                
    def register_widget(self, app):
        super().register_widget(app)
        
        @app.callback( 
            Output(self.id + "-box", "children"),
            Input("store-entity-selected","data"),
            State("store-Fiware-Service","data"),
            State("store-Fiware-Servicepath","data")
        )
        def refresh_custom(entity, service, path):
            print("REFRESHING CUSTOM", entity)
            if entity == None: raise PreventUpdate
            print("BUILDING")
            store = GetStoreDefaults()
            store["entity-selected"] = entity
            store["Fiware-Service"] = service
            store["Fiware-Servicepath"] = path
            return self.build_widget(store)
        
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
