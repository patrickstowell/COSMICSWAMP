import importlib
import glob
from dash import html

g_widgetslist = {}

def create_dynamic_widget( config, app, store ):
    """ Creates a Dynamic Widget from user JSON entry.
        Any runtime specific variables should be preloaded
        into the store.
        
        Requires config to have "id", "type", and "data".

    Args:
        config (dict): Standard dictionary containing widget parameters.
        app (_type_): _description_
        store (_type_): _description_

    Returns:
        _type_: _description_
    """
    
    if "id" not in config:
        raise AttributeError(f"ERROR : Widget JSON entry needs an ID! {config}")
    
    if "type" not in config:
        raise AttributeError(f"ERROR : Widget JSON entry needs a TYPE! {config}")
        
    # Required Variables
    widget_name = config["id"]
    widget_type = config["type"]
    
    # Optional variables
    widget_data = {}
    if "data" in config: 
        widget_data = config["data"]
    
    # If widget already created, just build as before
    print("RETURNING PREBUILT")
    if widget_type in g_widgetslist:
        return g_widgetslist[widget_type]["object"]
        
    # Try to load widget from base widget folder
    print("LOADING WIDGET", widget_type)
    widget_module = importlib.import_module("widgets." + widget_type)
    #         # raise ImportError(f"Failed to find widget of type : {widget_type} in widgets folder.")
    # else:
    #     try:
    #         widget_module = importlib.import_module("widgets." + widget_type)
    #     except:
    #         print("ERROR", f"Failed to load widget : {widget_type}")
    #         return html.Div(className="widget-load-fail")
    
    # Build the widget and register its callbacks
    widget_object = widget_module.plugin(config, app)
    return widget_object


    # # Update the list
    # g_widgetslist[widget_type] = config
    # g_widgetslist[widget_type]["object"] = widget_object
    # g_widgetslist[widget_type]["registered"] = False
    
    # # Construction occurs twice on load on purpose
    # # to see if it can be called multiple times on the server.
    # return g_widgetslist[widget_type]["object"].construct_widget(store)

