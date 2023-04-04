import datetime
import folium
import pandas as pd
import numpy as np
import requests
import json
from math import radians, sin, cos, sqrt, atan2


def get_minutes_from_datetime(str_timestamp):
    
    try:
        formater = "%Y-%m-%dT%H:%M:%S"
        timestamp = datetime.datetime.strptime(str_timestamp, formater)
    except ValueError as e:
        pass
    
    try:
        formater = "%Y-%m-%dT%H:%M:%S"
        timestamp = datetime.datetime.strptime(str_timestamp, formater)
    except ValueError as e:
        pass
    
    if (timestamp.hour * 60 + timestamp.minute) == 0:
        return 1440
    
    return timestamp.hour * 60 + timestamp.minute



def haversine_np(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km

def build_distance_matrix_osrm(df):
    latitude = np.array(df.lat.to_numpy().tolist())
    longitude = np.array(df.lng.to_numpy().tolist())
    
    locations=""
    n_orders = len(df)
    for i in range(n_orders):
        locations = locations + "{},{};".format(longitude[i], latitude[i])
    r = requests.get("http://router.project-osrm.org/table/v1/car/"+ locations[:-1])
    routes = json.loads(r.content)
    coords_index = { i: (latitude[i], longitude[i]) for i in range(df.shape[0])}
    time_matrix = pd.DataFrame(routes['durations'])
    
    return time_matrix

def build_distance_matrix(df):
    lat1 = np.array(df['lat'])
    lng1 = np.array(df['lng'])
    lat2 = lat1.reshape(-1, 1)
    lng2 = lng1.reshape(-1, 1)
    dist = haversine_np(lng1, lat1, lng2, lat2)
    return pd.DataFrame(dist, columns=df.index, index=df.index)


def build_time_matrix(df, avg_vehicle_speed=35):
    df = build_distance_matrix(df)
    return (df / avg_vehicle_speed) * 60



def plot_order_locations(df, location_coordinates, pdp=1):
    # Set up the colours based on well's purpose
    purpose_colour = {'DEPOT':'red', 'Restaurant':'green', 'Retailer':'blue', 'Business': 'orange'}
    if pdp==0:
        purpose_colour = {'DEPOT':'red', 'Pickup':'green', 'Delivery':'blue'}

    map = folium.Map(location=[location_coordinates.lat.mean(), location_coordinates.lng.mean()], 
                     zoom_start=10, control_scale=True)

    #Loop through each row in the dataframe
    for i,row in df.iterrows():
        #Setup the content of the popup
        iframe = folium.IFrame(f'Order ID: {str(row["order_ID"])} \n Order Weight: {str(row["order_wt"])} lbs \n Service time: {str(row["service_time"])} mins')

        #Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=200, max_width=200)

        try:
            icon_color = purpose_colour[row['order_type']]
        except:
            #Catch nans
            icon_color = 'gray'

        #Add each row to the map
        folium.Marker(location=[location_coordinates['lat'][i],location_coordinates['lng'][i]],
                      popup = popup, 
                      icon=folium.Icon(color=icon_color, icon='')).add_to(map)


    return map
