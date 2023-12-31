import geojson as geojsonlib
import json
import math
import numpy as np

def latlon_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in meters between two latitude/longitude points on the Earth's surface.

    :param lat1: Latitude of the first point in degrees.
    :param lon1: Longitude of the first point in degrees.
    :param lat2: Latitude of the second point in degrees.
    :param lon2: Longitude of the second point in degrees.
    :return: Distance in meters.
    """
    # Radius of the Earth in meters
    R = 6371000.0

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance
    distance = R * c

    return distance


def latlon_bearing_shift(lat1,lon1,bearing,distance):
        
    d = distance/1000.

    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert the bearing from degrees to radians
    # bearing = math.radians(bearing)

    # Convert the latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    # Calculate the new latitude
    lat2 = math.asin(math.sin(lat1) * math.cos(d / R) + math.cos(lat1) * math.sin(d / R) * math.cos(bearing))

    # Calculate the new longitude
    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(d / R) * math.cos(lat1), math.cos(d / R) - math.sin(lat1) * math.sin(lat2))

    # Convert the new latitude and longitude back to degrees
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)

    # Ensure the longitude is within the range [-180, 180]
    lon2 = (lon2 + 180) % 360 - 180

    return lat2, lon2



def coerce(data):
    if "coordinates" in data:
        return json.loads(json.dumps(data))
    elif "coordinates" not in data and "value" in data:
        return json.loads(json.dumps(data["value"]))
    else:
        print("UNSURE OF GEOJSON FORMAT", data)

def point(vals=[0.0,0.0], as_dict=True):
    p = geojsonlib.Point(vals)
    if as_dict: return json.loads(json.dumps(p))
    else: return p


def polygon(vals=[[0.,0.],[0.,1.],[1.,1.],[1.,0.],[0.,0.]], as_dict=True):
    p = geojsonlib.Polygon([vals])
    if as_dict: return json.loads(json.dumps(p))
    else: return p
    


def circle_around_point(point_in = None, radius=None, nsegments=12):

    if not point_in: point_in = point()
    if not radius: return point_in

    point_in = coerce(point_in)
    coords = point_in["coordinates"]

    segmentlist = []
    for i in range(nsegments):
        angle = -i*2*3.14159/float(nsegments)
        edgelat, edgelon = latlon_bearing_shift(coords[1], coords[0], angle, radius)
        segmentlist.append( [edgelon, edgelat] )

    # Close the polygon
    segmentlist.append( segmentlist[0] )


    p = polygon(segmentlist)
    print(point_in)
    print(p)

    return coerce(p)



def seperate_into_zones(circle):
    return ""


def split_lat_lon_from_polygon(coords):

    if "coordinates" not in coords:
        coords = coords["value"]
    print(coords)
    latlonlist = coords["coordinates"][0]
    print(latlonlist)

    latlist = []
    lonlist = []
    for val in latlonlist:
        latlist.append(val[1])
        lonlist.append(val[0])

    return latlist, lonlist

def mean_lat_lon_from_polygon(coords):

    latlonlist = coords["value"]["coordinates"][0]
    print(latlonlist)

    latlist = []
    lonlist = []
    for val in latlonlist:
        latlist.append(val[1])
        lonlist.append(val[0])

    return np.mean(latlist), np.mean(lonlist)

def mean_lon_lat_from_polygon(coords):

    latlonlist = coords["value"]["coordinates"][0]
    print(latlonlist)

    latlist = []
    lonlist = []
    for val in latlonlist:
        latlist.append(val[1])
        lonlist.append(val[0])

    return np.mean(lonlist), np.mean(latlist)



def split_lat_lon_from_points(coords):

    latlonlist = coords["value"]["coordinates"]

    return latlonlist[1], latlonlist[0]


def to_wgs84_list(coords):
    # print(coords)
    # if coords["type"] == "Point":
        # return str(coords["coordinates"][1]) + ";" + str(coords["coordinates"][0])
    if len(coords) == 2: 
        return str(coords[1]) + "," + str(coords[0])
    listdata = ""
    for c in coords[0]:
        listdata += str(c[1]) + "," + str(c[0]) + ";"
    listdata = listdata.strip(";")
    return listdata

def reverse_polygon(location):
    location["coordinates"][0].reverse()
    return location

def center_point_of_polygon(zoneloc):

    lat,lon = split_lat_lon_from_polygon(zoneloc)

    centrelat = np.mean(lat)
    centrelon = np.mean(lon)

    return {"value":point([centrelon,centrelat]), "type":"geo:json"}