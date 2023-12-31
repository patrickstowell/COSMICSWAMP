from base_plugin import base_plugin
from dash import html

default_style = {
    "padding": "5px"
}

# Simple Box Plugin
class plugin(base_plugin):
    def __init__(self, config, app):
        super().__init__(config)
        print("Building simple box", config)
        self.message = self.data
        
    def build_widget(self, store):
        print("Building Widget")
        super().build_widget(store)
        return html.Div(id=self.id, children=self.data["message"], style=self.style)
        
    def register_widget(self, app):
        super().register_widget(app)
        print("Registering Widget")