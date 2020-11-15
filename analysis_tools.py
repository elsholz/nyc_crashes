import pandas as pd
import ipywidgets as widgets
import matplotlib.pyplot as plt
from pylab import rcParams
import folium
from pymongo import MongoClient
from folium.plugins import HeatMap

with MongoClient('mongodb://localhost:27017/') as client:
    global database
    global crashes
    global crashes_by_year
    database = client["nyc_crashes"]
    crashes = database.crashes
    crashes_by_year = database.crashes_by_year


def monthly(Jahr):
    data = crashes_by_year.find_one({"_id": Jahr})['by_month']
    
    x_values = data.keys()
    y_values_injured = []
    y_values_killed = []
    for month in data:
        injured = 0
        killed = 0
        injured = data[month]['pedestrians']['injured'] + data[month]['cyclists']['injured'] + data[month]['motorists']['injured']
        killed = data[month]['pedestrians']['killed'] + data[month]['cyclists']['killed'] + data[month]['motorists']['killed']
        y_values_injured += [injured]
        y_values_killed += [killed]
    
    show_graph_injury(x_values, y_values_injured, y_values_killed)
    return


def monthly_sum(Jahr):
    data = crashes_by_year.find_one({"_id": Jahr})['by_month']
    
    x_values = data.keys()
    y_values_pedestrians = []
    y_values_cyclists = []
    y_values_motorists = []
    for month in data:
        pedestrians = 0
        cyclists = 0
        motorists = 0
        pedestrians = data[month]['pedestrians']['sum']
        cyclists = data[month]['cyclists']['sum']
        motorists = data[month]['motorists']['sum']
        y_values_pedestrians += [pedestrians]
        y_values_cyclists += [cyclists]
        y_values_motorists += [motorists]
    
    show_graph_type(x_values, y_values_pedestrians, y_values_cyclists, y_values_motorists)
    return


def show_graph_injury(x_values, y_values_injured, y_values_killed):
    plt.figure(figsize=(15,10))

    p1 = plt.bar(x_values, y_values_killed, color=(0.92,0.07,0.04))
    p2 = plt.bar(x_values, y_values_injured, bottom=y_values_killed, color=(0.90,0.90,0.00))

    plt.ylabel('Anzahl Unfaelle')
    plt.title('Unfaelle pro Monat nach Art')
    plt.legend((p2[0], p1[0]), ('Verletze', 'Todesfaelle'))
    plt.show()


def show_graph_type(x_values, y_values_pedestrians, y_values_cyclists, y_values_motorists):
    plt.figure(figsize=(15,10))
    
    p1 = plt.bar(x_values, y_values_motorists, color=(0.40,0.40,0.40))
    p2 = plt.bar(x_values, y_values_cyclists, bottom=y_values_motorists, color=(0.85,0.85,0.1))
    bottom_gold = [a+b for a,b in zip(y_values_cyclists, y_values_motorists)]
    p3 = plt.bar(x_values, y_values_pedestrians, bottom=bottom_gold, color=(0.10,0.8,0.10))
    
    plt.ylabel('Anzahl Unfaelle')
    plt.title('Unfaelle pro Monat nach Art')
    plt.legend((p3[0], p2[0], p1[0]), ('Fussgaenger', 'Fahrradfahrer', 'Personen in Fahrzeugen'))
    plt.show()


def make_map():
    all_inj, all_kil, ped_inj, ped_kil, \
    cyc_inj, cyc_kil, mot_inj, mot_kil = [[]] * 8
     
    layer_conf = {'zoom_start': 10.5, 'min_zoom': 10, 'max_zoom': 20}
    base_map = folium.Map(location=[40.73, -73.8], **layer_conf)
    
    with MongoClient('mongodb://localhost:27017') as client:    
        for idx, crash in enumerate(
            client['nyc_crashes']['crashes'].find({
                '$or': [
                    {'persons_injured': {'$gt': 0}},
                    {'persons_killed': {'$gt': 0}}
                ]}, 
                {
                    '_id': 0, 'latitude': 1, 'longitude':1, 
                    'persons_killed': 1, 'persons_injured': 1,
                    'pedestrians_killed': 1, 'pedestrians_injured': 1,
                    'cyclists_killed': 1, 'cyclists_injured': 1,
                    'motorists_killed': 1, 'motorists_injured': 1
            })):
            lon, lat = crash['longitude'], crash['latitude']
            coords = (lat, lon)
            if lon and lat:
                for atr, l in zip([
                    'persons_killed', 'persons_injured', 
                    'pedestrians_killed', 'pedestrians_injured', 
                    'cyclists_killed', 'cyclists_injured', 
                    'motorists_killed', 'motorists_injured'
                ], [ 
                    all_inj, all_kil, ped_inj, ped_kil, 
                    cyc_inj, cyc_kil, mot_inj, mot_kil
                ]):
                    if crash[atr]:
                        l.append(coords)
                
    HeatMap(name='All crashes with injuries', data=all_inj, radius=10, show=False).add_to(base_map)
    HeatMap(name='All crashes with fatalities', data=all_kil, radius=10, show=False).add_to(base_map)
    HeatMap(name='Cyclists injured', data=cyc_inj, radius=10, show=False).add_to(base_map)
    HeatMap(name='Cyclists killed', data=cyc_kil, radius=10, show=False).add_to(base_map)
    HeatMap(name='Pedestrians injured', data=ped_inj, radius=10, show=False).add_to(base_map)
    HeatMap(name='Pedestrians killed', data=ped_kil, radius=10, show=False).add_to(base_map)
    HeatMap(name='Motorists injured', data=mot_inj, radius=10, show=False).add_to(base_map)
    HeatMap(name='Motorists killed', data=mot_kil, radius=10, show=False).add_to(base_map)
    
    for layer in ['Stamen Terrain', 'Stamen Toner', 'Stamen Water Color']:
        folium.TileLayer(layer, **layer_conf).add_to(base_map)
    folium.LayerControl().add_to(base_map)
    
    return base_map
