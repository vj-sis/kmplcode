#!/usr/bin/env python
# coding: utf-8

# ## Importing Libraries ##
import pandas as pd
import numpy as np
from datetime import date
from datetime import timedelta
from datetime import datetime
import math


#custom functions
def filter_km(km_value):
    if abs(km_value) > 5:
        return 0
    return km_value



# In[1]:

def calculate_vitals(excel_path):


    #getting file names, vin number and registation numbers
    reg_number_index = pd.read_excel('vin_index.xlsx')
    vehicle_vin_number = excel_path.split("_")[0]
    print(vehicle_vin_number)

    reg_number_index.vin.to_list()
    reg_number_dict = {}
    for index, row in reg_number_index.iterrows():
        reg_number_dict[row.vin] = row.reg_number

    vehicle_reg_number = reg_number_dict[vehicle_vin_number]



    # ## Getting and cleaning the data ##
    raw_data = pd.read_excel(excel_path)

    # removing values which are blank, empty or zero
    data = raw_data.loc[(raw_data['packet_sequence_id'] != np.nan) & (raw_data['packet_sequence_id'] != "") & (raw_data['packet_sequence_id'] != 0) ].copy()

    #for column in data.columns:
    #    print(column)

    data['distance_covered'] = data['vehicle_odometer'] - data.shift(1)['vehicle_odometer']
    data.replace(np.nan,0, inplace = True )
    data['distance_covered'] = data.apply(lambda row: filter_km(row['distance_covered']), axis=1)
    data.distance_covered.sum()


    # ## Distance Travelled calculation
    # **Distance Travelled as per Vehicle ODO**

    #distance travelled as per vehicle odo
    distance_travelled_vehicle_odo = np.max(data[data['vehicle_odometer'] != 0]['vehicle_odometer'])- np.min(data[data['vehicle_odometer'] != 0]['vehicle_odometer'])
    print(f'Distance travelled as per vehicle odo is {distance_travelled_vehicle_odo:.1f} km')


    # **Distance travelled as per ECU ODO**
    vehicle_ecu_distance_readings = data[data['vehicle_distance'] != 0]['vehicle_distance']
    distance_travelled_ecu_odo = np.max(vehicle_ecu_distance_readings)-np.min(vehicle_ecu_distance_readings)
    print(f'Distance travelled as per vehicle odo is {distance_travelled_ecu_odo:.1f} km')

    # ## Fuel Consumption calculation ##
    fuel_consumption_readings = data[data['fuel_consumption'] != 0]['fuel_consumption']
    Fuel_consumption = np.max(fuel_consumption_readings)-np.min(fuel_consumption_readings)
    print(f'Fuel consumption is {Fuel_consumption} lts')

    # ## Running time calculations

    # **Active hours**
    #
    # Total number of packets/600
    total_active_hours = len(np.unique(data['packet_sequence_id']))/600
    print(f'Total active hours are {total_active_hours:.2f} hours')

    # **Running Hours**
    #
    # Total packets in below conditions / 600 <br>
    # - wheel base speed >=5 <br>
    # - engine speed >= 5
    running_packets = data.loc[(data['wheel_based_speed']>=5) & (data['engine_speed']>=5)  ]['packet_sequence_id'].copy()
    total_running_hours = len(np.unique(running_packets))/600
    print(f'Total running hours are {total_running_hours:.2f} hours')

    # **Idling Hours** <br>
    # <br>
    # Total packets in below conditions / 600 <br>
    # - wheel base speed < 5 <br>
    # - engine speed <5
    idling_packets = data.loc[(data['wheel_based_speed']<5) & (data['engine_speed']>5)  ]['packet_sequence_id'].copy()
    total_idling_hours = len(np.unique(idling_packets))/600
    print(f'Total idling hours are {total_idling_hours:.2f} hours')

    # **Neutral driving hours**<br><br>
    # Total packets in below conditions / 600 <br>
    # - wheel base speed >= 5<br>
    # - engine speed > = 5<br>
    # - clutch pedal = 0<br>
    # - gear = 0
    neutral_driving_packets = data.loc[(data['wheel_based_speed']>=5) & (data['engine_speed']>=5)  & (data['clutch_pedal'] == 0) & (data['transmission_current_gear'] == 0)]['packet_sequence_id'].copy()
    total_neutral_driving_hours = len(np.unique(neutral_driving_packets))/600
    print(f'Total neutral driving hours are {total_neutral_driving_hours:.2f} hours')

    # **Zero throttle running distance**
    # <br>
    # <br>
    # Total packets in below condition /600
    # - Throttle position = 0
    # - wheel based speed = 0
    zero_throttle_packets = data.loc[(data['throttle_position']==0) & (data['wheel_based_speed']>5)  ]['distance_covered'].copy()
    zero_throttle_running_distance = np.sum(zero_throttle_packets)
    print(f'Total zero throttle running distance is {zero_throttle_running_distance:.2f} km')

    # ## Day time/Night time running calculation
    # **Daytime running distance** = Distance travelled between 5AM and 9PM
    first_day = data.iloc[0]['obu_timestamp']
    last_day = data.iloc[-1]['obu_timestamp']
    first_day_datetime = datetime.combine(first_day.date(), datetime.min.time())
    last_day_datetime = datetime.combine(last_day.date(), datetime.max.time())
    total_number_of_days = (last_day_datetime - first_day_datetime).days + 1
    dates_list_5am = []
    dates_list_9pm = []
    for i in range(total_number_of_days):
        dates_list_5am.append(first_day_datetime + timedelta(days = i) + timedelta(hours = 5))
        dates_list_9pm.append(first_day_datetime + timedelta(days = i) + timedelta(hours = 21))

    day_time_running_distance = 0

    for i in range(len(dates_list_5am)):
        daytime_day = data.loc[(data['obu_timestamp'] > dates_list_5am[i]) & (data['obu_timestamp'] < dates_list_9pm[i])]
        max_odo = np.max(daytime_day[daytime_day['vehicle_odometer'] != 0]['vehicle_odometer'])
        min_odo = np.min(daytime_day[daytime_day['vehicle_odometer'] != 0]['vehicle_odometer'])
        #print(min_odo,max_odo)

        if(not (math.isnan(max_odo) and math.isnan(min_odo))):
            total_running_km = max_odo-min_odo
            day_time_running_distance += total_running_km


    night_time_running_distance = distance_travelled_vehicle_odo - day_time_running_distance

    print(f'Total day time running distance is {day_time_running_distance:.2f} km')
    print(f'Total night time running distance is {night_time_running_distance:.2f} km')
    average_speed = distance_travelled_vehicle_odo / total_active_hours
    halt_hours = total_number_of_days*24 - total_running_hours - total_idling_hours
    running_percentage = (total_running_hours/total_active_hours)
    idling_percentage = (total_idling_hours/total_active_hours)

    print(f'Average speed of the vehicle is {average_speed:.2f} km/h ')
    print(f'Total halt hours are {halt_hours:.2f} hrs')
    print(f'Running % is {(running_percentage * 100):.2f} %')
    print(f'Idling % is {(idling_percentage*100):.2f} %')


    # ## Pivot for Vehicle Speed Vs Distance ##
    groups= data.groupby([pd.cut(data.wheel_based_speed, np.arange(0, 110, 10), right = False)], dropna= False)
    speed_vs_distance_covered_df = groups.distance_covered.sum().to_frame()
    tot_distance = np.sum(speed_vs_distance_covered_df.distance_covered)
    speed_vs_distance_covered_df[vehicle_vin_number] = speed_vs_distance_covered_df['distance_covered']/tot_distance

    speed_vs_distance_covered_df.columns = [vehicle_reg_number, vehicle_reg_number + "percentage" ]


    # ## Pivot for Throttle Vs Distance ##
    data_throttle = data[data['engine_speed'] > 0]
    groups= data_throttle.groupby([pd.cut(data.throttle_position, np.arange(-9, 120, 10))], dropna= False)
    throttle_vs_distance_covered_df = groups.distance_covered.sum().to_frame()
    tot_distance = np.sum(throttle_vs_distance_covered_df['distance_covered'])
    throttle_vs_distance_covered_df['distance_travelled_percentage'] = throttle_vs_distance_covered_df['distance_covered']/tot_distance
    throttle_vs_distance_covered_df['distance_covered'].sum()
    throttle_vs_distance_covered_df.columns = [vehicle_reg_number, vehicle_reg_number + "percentage"]


    # ## Torque vs Distance Covered ##
    groups= data_throttle.groupby([pd.cut(data.actual_engine_percent_torque, np.arange(-10, 120, 10))], dropna= False)
    torque_vs_distance_covered_df = groups.distance_covered.sum().to_frame()
    tot_distance = np.sum(torque_vs_distance_covered_df['distance_covered'])
    torque_vs_distance_covered_df['distance_covered_percent'] = torque_vs_distance_covered_df['distance_covered']/tot_distance
    torque_vs_distance_covered_df.columns = [vehicle_reg_number, vehicle_reg_number + "percentage"]

    # ## Engine Speed vs Distance Covered
    groups= data.groupby([pd.cut(data.engine_speed, np.arange(0, 2600, 200), right = False)], dropna= False)
    enginespeed_vs_distance_covered_df = groups.distance_covered.sum().to_frame()
    tot_distance = np.sum(enginespeed_vs_distance_covered_df.distance_covered)
    enginespeed_vs_distance_covered_df['distance_covered_percent'] = enginespeed_vs_distance_covered_df['distance_covered']/tot_distance
    enginespeed_vs_distance_covered_df.columns = [vehicle_reg_number, vehicle_reg_number + "percentage"]

    # ## Gear vs Distance Covered
    groups = data[data['wheel_based_speed']>5].groupby(by = 'transmission_current_gear', dropna = True)
    gear_vs_distance_covered_df = groups.distance_covered.sum().to_frame()
    gear_vs_distance_covered_df
    tot_distance = np.sum(gear_vs_distance_covered_df['distance_covered'])
    gear_vs_distance_covered_df['distance_covered_percent'] = gear_vs_distance_covered_df['distance_covered']/tot_distance
    gear_vs_distance_covered_df.columns = [vehicle_reg_number, vehicle_reg_number + "percentage"]

    table_dict = {}

    table_dict["Distance travelled(ECU Distance)"] = distance_travelled_ecu_odo
    table_dict["Distance travelled (Vehicle odometer)"] = distance_travelled_vehicle_odo
    table_dict["Fuel Consumption"]= Fuel_consumption
    table_dict["KMPL ECU distance"] = Fuel_consumption/distance_travelled_ecu_odo
    table_dict["KMPL Vehicle ODO"] = Fuel_consumption/distance_travelled_vehicle_odo
    table_dict["Total hours"] = total_active_hours
    table_dict["Total running hours"] = total_running_hours
    table_dict["Total idling hours"] = total_idling_hours
    table_dict["Halt time"] = halt_hours
    table_dict["Running percentage"] = running_percentage
    table_dict["Idling percentage"] = idling_percentage
    table_dict["Average Speed"] = average_speed
    table_dict["Total Neutral Driving Hours"] = total_neutral_driving_hours
    table_dict["Day time running distance"] = day_time_running_distance
    table_dict["Night time running distance"] = night_time_running_distance
    table_dict["Throttle 0 percent running distance"] = zero_throttle_running_distance


    vitals_df = pd.DataFrame.from_dict(table_dict, orient ='index', columns = [vehicle_reg_number] )

    result_dict = {}

    result_dict['vitals'] = vitals_df
    result_dict['speed_vs_distance_covered'] = speed_vs_distance_covered_df
    result_dict['torque_vs_distance_covered'] = torque_vs_distance_covered_df
    result_dict['throttle_vs_distance_covered'] = throttle_vs_distance_covered_df
    result_dict['engine_speed_vs_distance_covered'] = enginespeed_vs_distance_covered_df
    result_dict['gear_vs_distance_covered'] = gear_vs_distance_covered_df

    return(result_dict)


if __name__ == "__main__":
    results = calculate_vitals("MB1CWKHD6LPBL5666_result.xlsx")
    print(results)