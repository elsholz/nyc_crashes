import pandas as pd
import ipywidgets as widgets
import matplotlib.pyplot as plt
from pylab import rcParams
import folium
from pymongo import MongoClient
from folium.plugins import HeatMap
import numpy as np
import matplotlib
#rcParams['figure.figsize'] = 25, 13
font = {'size'   : 18}
matplotlib.rc('font', **font)
import matplotlib.patches as mpatches

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
        injured = data[month]['pedestrians']['injured'] + data[month]['cyclists']['injured'] + data[month]['motorists'][
            'injured']
        killed = data[month]['pedestrians']['killed'] + data[month]['cyclists']['killed'] + data[month]['motorists'][
            'killed']
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
    data = crashes_by_year.find_one({"_id": '2020'})['by_month']

    labels = x_values
    y_values_injured = y_values_injured
    y_values_killed = y_values_killed

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, y_values_injured, width, label='Verletzte')
    rects2 = ax.bar(x + width/2, y_values_killed, width, label='Todesfaelle')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Anzahl Unfaelle')
    ax.set_title('Unfaelle pro Monat nach Art der Verletzung')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)

    fig.tight_layout()
    
    plt.figure(figsize=(20, 11))

    p1 = plt.bar(x_values, y_values_killed, color=(0.92, 0.07, 0.04))
    p2 = plt.bar(x_values, y_values_injured, bottom=y_values_killed, color=(0.90, 0.90, 0.00))

    plt.show()


def show_graph_type(x_values, y_values_pedestrians, y_values_cyclists, y_values_motorists):
    plt.figure(figsize=(20, 11))

    p1 = plt.bar(x_values, y_values_motorists, color=(0.40, 0.40, 0.40))
    p2 = plt.bar(x_values, y_values_cyclists, bottom=y_values_motorists, color=(0.85, 0.85, 0.1))
    bottom_gold = [a + b for a, b in zip(y_values_cyclists, y_values_motorists)]
    p3 = plt.bar(x_values, y_values_pedestrians, bottom=bottom_gold, color=(0.10, 0.8, 0.10))

    plt.ylabel('Anzahl Unfaelle')
    plt.title('Unfaelle pro Monat nach Mobilitaetstyp')
    plt.legend((p3[0], p2[0], p1[0]), ('Fussgaenger', 'Fahrradfahrer', 'Personen in Fahrzeugen'))
    plt.show()


def show_line_chart(damage='killed', kinds=['pedestrians', 'motorists', 'cyclists']):
    """Line chart of injuries per vehicle-class per month from 2013 to 2019"""
    plt.figure(figsize=(20, 12))
    x = list(range(1, 13))

    for kind in kinds:
        yn = {}
        for year in crashes_by_year.find():
            months = {}
            for m in x:
                if (mdata := year.get('by_month', {}).get(str(m), {})):
                    months[m] = mdata.get(kind, {}).get(damage, None)
            yn[year['_id']] = months

        for y in sorted(yn, key=lambda x: int(x)):
            months = yn[y]
            plt.plot(list(months.keys()), list(months.values()), linewidth=15, color={
                'pedestrians': (1.0, 0.0, 0, 0.5),
                'cyclists': (.0, 1.0, 0, 0.5),
                'motorists': (0.5, 0.5, 0.5, 0.3),
            }[kind])

    green = mpatches.Patch(color='green', label='The red data')
    yellow = mpatches.Patch(color='yellow', label='The red data')
    gray = mpatches.Patch(color='gray', label='The red data')

    plt.legend(handles=[yellow, gray, green], labels=['pedestrians', 'motorists', 'cyclists'])
    plt.show()


def show_stacked_victims():
    years = sorted([y['_id'] for y in crashes_by_year.find()], key=lambda x: int(x))

    plt.figure(figsize=(20,12))
    plt.stackplot(
        years, [
            [crashes_by_year.find_one({'_id': {'$eq': year}})['whole_year']['pedestrians']['sum'] for year in years],
            [crashes_by_year.find_one({'_id': {'$eq': year}})['whole_year']['cyclists']['sum'] for year in years],
            [crashes_by_year.find_one({'_id': {'$eq': year}})['whole_year']['motorists']['sum'] for year in years],
        ],
        labels=['Pedestrians', 'Cyclists', 'Motorists'],
        alpha=0.9,
        colors=['yellow', 'green', 'lightgray']
    )

    # plt.legend(loc=2, fontsize='large')
    plt.legend()
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
                        '_id': 0, 'latitude': 1, 'longitude': 1,
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
