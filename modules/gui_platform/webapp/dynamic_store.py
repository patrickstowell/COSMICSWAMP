# import json
# import dash_core_components as dcc
# from dash import Dash, html
# from dash.dependencies import State, Input, Output


# def DynamicStore(app, filename=""):
#     """ Builds the requirements for a dynamic store system which
#     can be used to determine which entries in a JSON table have changed.
#     This allows a more flexible store callback system in development, but
#     has additional overhead as it requires a clone of a users store
#     inside their browser.

#     Args:
#         filename (str): Filename for a json file containing default store
#                         values used when instantiating JSON objects.

#     Returns:
#         store (dict) : Default store properties object.
#         store_header (html.Div) : Dash component necessary for including the store in layouts.
#     """
    
#     # Load Store defaults
#     store = {}
#     if filename != "":
#         store = json.load( open(filename, "r") )
        
#     # Build dash components
#     header = html.Div([
#         dcc.Store(id="store-local", data=store), 
#         dcc.Store(id="store-changed", data=store), 
#         dcc.Store(id="store-last", data=store)
#     ], id="store-header")
    
#     # Register the store
#     @app.callback(
#             Output("store-changed","data"),
#             Output("store-last", "data"),
#             Input("store-local","data"),
#             State("store-changed", "data"),
#             State("store-last", "data"),
#         )
#     def update(store_local, store_changed, store_last):
#         temp_store = {}
#         for key in store_local:
#             if key not in store_last or store_local[key] != store_last[key]:
#                 temp_store[key] = store_local[key]
        
#         return temp_store, store_local
        
#     return store, header