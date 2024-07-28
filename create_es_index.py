from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
import numpy as np

INDEX_NAME = "addresses"

es = Elasticsearch("http://127.0.0.1:9200")

body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "label": {
                "type": "text"
            },
            "coordinates": {
                "type": "geo_point"
            },
            "embedding": {
                "type": "dense_vector",
                "dims": 1024,
            }
        }
     }
}

es.indices.create(index=INDEX_NAME, body=body)


def read_str_field(source):
    field_size = int.from_bytes(source.read(8))
    return source.read(field_size).decode()


def read_numpy_field(source):
    field_size = int.from_bytes(source.read(8))
    return np.frombuffer(source.read(field_size), dtype=np.float32)


def read_line(source):
    return read_str_field(source), read_str_field(source) ,read_str_field(source), read_numpy_field(source)


def get_data():
    with open("addresses.csv", "rb") as source:
        i = 0
        while True:
            try:
                label, lat, lon, embedding = read_line(source)
                document = {
                    "_index":INDEX_NAME,
                    "_id": i,
                    "_source": {
                        "label": label,
                        "coordinate": {"lat": lat, "lon": lon},
                        "embedding": embedding,
                    },
                }
                yield document
                i += 1
            except Exception:
                break


for success, info in parallel_bulk(es, get_data(), thread_count=8, queue_size=8):
    if not success:
        print('A document failed:', info)
