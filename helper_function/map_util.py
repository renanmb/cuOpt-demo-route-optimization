import requests
import folium
import polyline
import folium.plugins as plugins

def get_route(pickup_lon, pickup_lat, dropoff_lon, dropoff_lat):
    
    loc = "{},{};{},{}".format(pickup_lon, pickup_lat, dropoff_lon, dropoff_lat)
    url = "http://router.project-osrm.org/route/v1/driving/"
    r = requests.get(url + loc) 
    if r.status_code!= 200:
        return {}
  
    res = r.json()   
    routes = polyline.decode(res['routes'][0]['geometry'])
    start_point = [res['waypoints'][0]['location'][1], res['waypoints'][0]['location'][0]]
    end_point = [res['waypoints'][1]['location'][1], res['waypoints'][1]['location'][0]]
    distance = res['routes'][0]['distance']
    
    out = {'route':routes,
           'start_point':start_point,
           'end_point':end_point,
           'distance':distance
          }

    return out



def get_all_routes(plot_map_df):
    route_list = dict()
    for i in range(len(plot_map_df)):
        pickup_lat = plot_map_df.iloc[i]['order_lat']
        pickup_lon = plot_map_df.iloc[i]['order_long']
        dropoff_lat = plot_map_df.iloc[i]['end_lat']
        dropoff_lon = plot_map_df.iloc[i]['end_long']
        route_list[i] = get_route(pickup_lon, pickup_lat, dropoff_lon, dropoff_lat) 
    return route_list


def get_map(route):
    
    m = folium.Map(location=[(route['start_point'][0] + route['end_point'][0])/2, 
                             (route['start_point'][1] + route['end_point'][1])/2], 
                   zoom_start=13)

    folium.PolyLine(
        route['route'],
        weight=4,
        color='blue',
        opacity=0.6
    ).add_to(m)

    folium.Marker(
        location=route['start_point'],
        icon=folium.Icon(color="green",icon="fa-building", prefix='fa')
    ).add_to(m)

    folium.Marker(
        location=route['end_point'],
        icon=folium.Icon(color="red",icon="fa-truck", prefix='fa')
    ).add_to(m)

    return m



def get_map_by_vehicle(filtered_dict):
    m = folium.Map(location=[32.769792748967795, -96.79335979538052], zoom_start = 9)
    new_dict = {k: v for k, v in filtered_dict.items() if v['distance'] != 0}
    count = 0
    for idx, route in new_dict.items():
        
        folium.Map(location=[(route['start_point'][0] + route['end_point'][0])/2, 
                                 (route['start_point'][1] + route['end_point'][1])/2], 
                       zoom_start=11).add_to(m)

        folium.PolyLine(
            route['route'],
            weight=4,
            color='blue',
            opacity=0.6
        ).add_to(m)
        
        if count == 0:
            folium.Marker(
                location=route['start_point'],
                icon=folium.Icon(color="green",icon="fa-building", prefix='fa')
            ).add_to(m)
            
            
            folium.Marker(
                location=route['end_point'],
                #icon=folium.Icon(color="red",icon="fa-map-pin", prefix='fa')
                icon=plugins.BeautifyIcon(
                         icon="arrow-down", icon_shape="marker",
                         number=count+1,
                         border_color= 'red',
                     )
            ).add_to(m)
        else:
            """
            folium.Marker(
                location=route['start_point'],
                icon=folium.Icon(color="blue",icon="fa-map-pin", prefix='fa')
            ).add_to(m)
            """
            folium.Marker(
                location=route['end_point'],
                icon=plugins.BeautifyIcon(
                         icon="arrow-down", icon_shape="marker",
                         number=count+1,
                         border_color= 'red',
                     )
            ).add_to(m)
        count += 1  
    return m