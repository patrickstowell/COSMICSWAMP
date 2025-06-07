from ipyleaflet import *
from ipywidgets import Layout

def build_map(latlon : dict, zoom : int = 12):
        
    center = (latlon[1],latlon[0])
    zoom = zoom

    mapnik = basemap_to_tiles(basemaps.OpenStreetMap.Mapnik)
    mapnik.base = True
    mapnik.name = 'Mapnik Layer'

    bzh = basemap_to_tiles(basemaps.OpenStreetMap.BZH)
    bzh.base = True
    bzh.name = 'BZH layer'

    defaultLayout=Layout(width='960px', height='540px')
    zoom = 16

    m = Map(center=center, 
            zoom=zoom, layers=[mapnik], interpolation="nearest", layout=defaultLayout)
    m.layout.height = '600px'
    satelite_url = 'http://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}'
    satelite_provider = TileLayer(url=satelite_url, opacity=1, subdomains=['mt0','mt1','mt2','mt3'])
    satelite_group = LayerGroup(name="Satellite",layers=[satelite_provider])
    m.add_layer(satelite_group)

    return m

def display_map(m):
    display(m)