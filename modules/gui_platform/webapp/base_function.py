import dash_draggable
from dash import html
from dash import Dash, dcc, html, Input, Output


def jst(data):
    style = {}
    for keys in data.split(";"):
        vals = keys.split(":")
        if len(vals) <= 1: continue
        style[ vals[0].strip() ] = vals[1].strip()
    return style
            
default_style = {
    "padding": "5px"
}    
            
# Simple Box Plugin
class base_function:
    def __init__(self, config):
        self.config = config
        self.id     = config["id"]
        self.type   = config["type"]            
        self.style = default_style
        
        if "style" in config:
            self.merge_styles( self.style, config["style"])
        
    def build_widget(self, store):
        print(f"{self.id} : Building function")
        return "" 
        
    def construct_widget(self, store):
        content = self.build_widget(store)
        
        return html.Div(id=self.id + "-box", 
                        children=content)
    
    def merge_styles(self, style1, style2):
        for key in style2:
            style1[key] = style2[key]
        
    
    def register_widget(self, app):
        print(f"[{self.id}] Registering callbacks.")