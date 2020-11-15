import folium
from pymongo import MongoClient
from folium.plugins import HeatMap


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
crash_map = base_map
