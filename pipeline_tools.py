from pymongo import MongoClient
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
import pandas as pd
import re
from pathlib import Path
import csv


def send_to_kafka(topic, limit=None):
    print(f'Started {topic} Producer process.')
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

    with open((fn := Path('data') / f'{topic}.csv')) as source:
        for counter, row in enumerate(source.readlines()):
            if limit and counter >= limit:
                producer.close()
                print(f'Producer for topic {topic} closed after {counter + 1} entries.')
                return counter - 1
            if counter:
                producer.send(f'nyc_{topic}', value=bytearray(row, encoding='utf-8'),
                              key=bytearray(str(counter), encoding='utf-8'))
            if not counter % 100000 and counter:
                print(f'CSV → Kafka: Read {counter} lines from {fn}.')
        producer.close()
        print(f'Producer for topic {topic} closed after {counter - 1} entries.')
        return counter - 1


def process_topic(topic, types, limit=None):
    errors = {}
    with MongoClient("mongodb://localhost:27017") as client:
        target_db = client['nyc_crashes'][topic]
        if topic == 'crashes':
            db = client['nyc_crashes']
            db['persons'].create_index('collision_id')
            db['vehicles'].create_index('collision_id')

        consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'], auto_offset_reset='earliest')
        consumer.subscribe([f'nyc_{topic}'])
        print(f'Started {topic} Consumer process.')

        for counter, row in enumerate(consumer):
            row = row.value.decode('utf-8')

            if counter and not counter % 100000:
                with open(f'log{topic}', 'w') as fout:
                    fout.write(str(errors))
                print(f'Kafka → MongoDB: Read {counter} lines from Kafka topic {topic}.')
            for line in csv.reader([row]):
                res = {}
                for idx, (db_field, field_type) in enumerate(types.items()):
                    try:
                        if row_data := line[idx]:
                            res[db_field] = field_type.__call__(row_data) if not isinstance(row_data,
                                                                                            field_type) else row_data
                        else:
                            res[db_field] = None
                    except Exception as e:
                        res[db_field] = None
                        errors[type(e)] = errors.get(type(e), 0) + 1

            if res['_id']:
                try:
                    if topic == 'crashes':
                        try:
                            res['vehicles'] = list(db['vehicles'].find({'collision_id': {'$eq': res['_id']}}))
                        except Exception as e:
                            errors[type(e)] = errors.get(type(e), 0) + 1
                        try:
                            res['persons'] = list(db['persons'].find({'collision_id': {'$eq': res['_id']}}))
                        except Exception as e:
                            errors[type(e)] = errors.get(type(e), 0) + 1
                        try:
                            res['year'] = (date := datetime.strptime(res['crash_date'], "%m/%d/%Y")).year
                            res['month'] = date.month
                            res['day'] = date.day
                        except Exception as e:
                            errors[type(e)] = errors.get(type(e), 0) + 1

                    target_db.insert_one(res)
                except Exception as e:
                    errors[type(e)] = errors.get(type(e), 0) + 1
            else:
                errors['No _id!!'] = errors.get('No _id!!', 0) + 1
            if limit and limit - 1 == counter:
                print(f'Consumer for topic {topic} closed after {counter + 1} entries.')
                consumer.close()
                with open(f'log{topic}', 'w') as fout:
                    fout.write(str(errors))
                return


def aggregate_data():
    # TODO: add `all` field: inter-kind sum of killed/ injured/ kind-sum
    with MongoClient("mongodb://localhost:27017") as client:
        crashes_by_year = client['nyc_crashes']['crashes_by_year']
        collection = client['nyc_crashes']['crashes']
        years = {}
        kinds = ['pedestrians', 'cyclists', 'motorists']

        for crash in collection.find({}):
            # TODO: remove
            crash['year'] = (date := datetime.strptime(crash['crash_date'], "%m/%d/%Y")).year
            crash['month'] = date.month
            crash['day'] = date.day
            cy = crash['year']
            cm = crash['month']
            cd = crash['day']


            years[cy] = years.get(cy, [])
            years[cy].append((cm, cd, {
                kind:
                    {
                        'injured': (i := crash[f'{kind}_injured']),
                        'killed': (k := crash[f'{kind}_killed']),
                        'sum': (i + k)
                    }
                for kind in kinds
            }))

        for year, crashes in years.items():
            crashes_by_year.insert_one({
                '_id': str(year),
                'by_month': {
                    str(month): {
                        kind: {
                            'injured': (i := sum(c[2][kind]['injured'] for c in crashes if c[0] == month)),
                            'killed': (k := sum(c[2][kind]['killed'] for c in crashes if c[0] == month)),
                            'sum': k + i
                        } for kind in kinds
                    } for month in range(1, 13)
                },
                'whole_year': {
                    kind: {
                        'injured': (i := sum(c[2][kind]['injured'] for c in crashes)),
                        'killed': (k := sum(c[2][kind]['killed'] for c in crashes)),
                        'sum': k + i
                    } for kind in kinds
                }
            })


