import cudf
import cuopt
from cuopt.routing import utils
import pandas as pd
# Reads one of the homberger's insatnce definition to read dataset
# This function is specifically desgined only to read homberger's insatnce definition
def read_data(filename):
    df, vehicle_capacity, n_vehicles = utils.create_from_file(filename)
    return df, vehicle_capacity, n_vehicles




import time

def get_dates_time_from_minutes(mins, date="2022-04-26T", format="%H:%M:%3SZ"):
    return date+time.strftime(format, time.gmtime(mins*60))

def get_time_travelled(veh_idx, routes, time_travelled):
    routes = routes.loc[veh_idx]
    return sum([float(time_travelled[routes["location"].iloc[idx+1]].iloc[routes["location"].iloc[idx]]) for idx in range(len(routes)-1)])
    
def get_distance_travelled(veh_idx, routes, distance):
    routes = routes.loc[veh_idx]
    return sum([float(distance[routes["location"].iloc[idx+1]].iloc[routes["location"].iloc[idx]]) for idx in range(len(routes)-1)])
    
def get_jobs(veh_id, routes, jobs):
    routes = routes.loc[veh_id]
    if isinstance(routes, pd.DataFrame):
        return {
            jobs["order_ID"].iloc[routes['location'].iloc[job_id]]: {
                "delivery_start"   : jobs["delivery_start"].iloc[routes['location'].iloc[job_id]],
                "delivery_end"     : jobs["delivery_end"].iloc[routes['location'].iloc[job_id]],
                "actualBeginTime"  : get_dates_time_from_minutes(routes['arrival_stamp'].iloc[0]),
                "actualEndTime"    : get_dates_time_from_minutes(routes['arrival_stamp'].iloc[-1]),
                "service_time"     : routes['arrival_stamp'].iloc[-1] - routes['arrival_stamp'].iloc[0],
                "latitude"         : jobs['lat'].iloc[routes['location'].iloc[job_id]],
                "longitude"        : jobs['lng'].iloc[routes['location'].iloc[job_id]]
            }
            for job_id in range(len(routes))
        }
    else:
        return {
            jobs["order_ID"].iloc[routes["location"]]: {
                "delivery_start" : jobs["delivery_start"].iloc[routes['location']],
                "delivery_end" : jobs["delivery_end"].iloc[routes['location']],
                "actualBeginTime" : get_dates_time_from_minutes(routes['arrival_stamp']),
                "actualEndTime" : get_dates_time_from_minutes(routes['arrival_stamp'] + jobs["service_time"].iloc[routes['location']]),
                "service_time" : routes['arrival_stamp'] + jobs["service_time"].iloc[routes['location']],
                "latitude"         : jobs['lat'].iloc[routes['location'].iloc[job_id]],
                "longitude"        : jobs['lng'].iloc[routes['location'].iloc[job_id]]
            }
        }

def get_details_for_single_job_route(idx, routes, jobs, techs):
    tmp_routes = routes.loc[idx]
    return {
        "vehicle_start" : techs["vehicle_start"].iloc[idx],
        "vehicle_end"   : techs["vehicle_end"].iloc[idx],
        "actualStart"   : get_dates_time_from_minutes(routes['arrival_stamp'].loc[idx]),
        "actualEnd"     : get_dates_time_from_minutes(routes['arrival_stamp'].loc[idx] + jobs["service_time"].iloc[tmp_routes['location']]),
        "distance"      : 0,
        "time_travelled": 0,
        "truck_id"      : idx,
        "jobs"          : get_jobs(idx, routes, jobs)
        
    }


def get_tech_job_details(routes, orders, vehicles, distance, time_travelled):
    return {
        vehicles["vehicle_id"].iloc[idx] : {
            "vehicle_start" : vehicles["vehicle_start"].iloc[idx],
            "vehicle_end"   : vehicles["vehicle_end"].iloc[idx],
            "tech_available_time" : vehicles["vehicle_end_in_minutes"].iloc[idx] - vehicles["vehicle_start_in_minutes"].iloc[idx],
            "actualStart"   : get_dates_time_from_minutes(routes['arrival_stamp'].loc[idx].iloc[0]),
            "actualEnd"     : get_dates_time_from_minutes(routes['arrival_stamp'].loc[idx].iloc[-1]),
            "actualStart_minutes"   : routes['arrival_stamp'].loc[idx].iloc[0],
            "actualEnd_minutes"     : routes['arrival_stamp'].loc[idx].iloc[-1],
            "distance"      : get_distance_travelled(idx, routes, distance),
            "time_travelled": get_time_travelled(idx, routes, time_travelled),
            "truck_id"      : idx,
            "work_time"     : sum(v["service_time"] for v in get_jobs(idx, routes, orders).values()),
            "latitude"      : vehicles["lat"].iloc[idx],
            "longitude"      : vehicles["lng"].iloc[idx],
            "orders" : get_jobs(idx, routes, orders)
        }  if isinstance(routes['arrival_stamp'].loc[idx], pd.Series) else  get_details_for_single_job_route(idx, routes, orders, vehicles) for idx in routes.index.unique()}






def parse_output_summary(solution, n_orders, n_vehicles, orders_details, vehicle_df, location_coordinates, distance_matrix, time_matrix, n_depot=1):
    print("\n" + '\033[1m' + "Output Summary:" + '\033[0m')
    
    if solution.get_status() == 0:
        routes_df = solution.get_route().to_pandas()
        routes_df = routes_df[routes_df['type'] == "Delivery"]
        
        assigned_orders = orders_details.iloc[list(routes_df.location.unique())]
        # get the indexes not in list_a
        unassigned_orders_idx = set(orders_details.index) - set(list(routes_df.location.unique()))
        unassigned_orders = orders_details.iloc[list(unassigned_orders_idx)]
        
        print("\tTotal Available Orders: ", n_orders-n_depot)
        print("\tTotal Orders Assigned to be delivered : ", len(assigned_orders))
        
        r_df = solution.get_route().to_pandas().set_index("truck_id")
        r_df = r_df[r_df.index < n_vehicles]
        r_df = r_df[r_df.route < n_orders]
        
        c = get_tech_job_details(r_df, orders_details, vehicle_df, distance_matrix.to_pandas(), time_matrix.to_pandas())
        
        print("Tech Job Details:")
        print("\tVehicles Available : ", n_vehicles)
        print("\tVehicles Assigned : ", len(c))
        
    return c


def prepare_data_for_maps(depot_df, output):
    map_df = pd.DataFrame(columns = ['vehicle_id', 'order_id', 'order_lat', 'order_long', 'end_lat', 'end_long'])
    
    flag = 0
    for k, v in output.items():
        for m, n in v['orders'].items():
            map_df.loc[flag] = [int(k), int(m), n['latitude'], n['longitude'], 0, 0]
            flag = flag + 1
    map_df = map_df.astype({"vehicle_id": int, "order_id": int})
    map_df['end_lat'] = map_df['order_lat'].shift(-1)
    map_df['end_long'] = map_df['order_long'].shift(-1)
    
    value_counts = map_df['vehicle_id'].value_counts()[map_df['vehicle_id'].unique()]
    value_counts = value_counts.cumsum()
    for idx, val in value_counts.iteritems():
        map_df.loc[val-1, 'end_lat'] = map_df.loc[val-1, 'order_lat']
        map_df.loc[val-1, 'end_long'] = map_df.loc[val-1, 'order_long']
    return map_df