import json

from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk

INDEX_NAME = "toilets"

es = Elasticsearch("http://127.0.0.1:9200")

body = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "coordinate": {
                "type": "geo_point"
            },
            "fee": {
                "type": "text"
            },
            "weelchair": {
                "type": "text"
            }
        }
     }
}

es.indices.create(index=INDEX_NAME, body=body)


def get_data():
    with open("eu_toilets.json", "r", encoding="utf-16-le") as source:
        for i, line in enumerate(source):
            entry = json.loads(line.replace("\ufeff", ""))

            # ignoring non public toilets
            
            if not "access" in entry["tags"] or entry["tags"]["access"] in ("yes", "public"):
                if entry["type"] == "node":
                    lat, lon = float(entry["lat"]), float(entry["lon"])
                else:
                    lat, lon = float(entry["centroid"]["lat"]), float(entry["centroid"]["lon"])

                document = {
                    "_index":INDEX_NAME,
                    "_id": i,
                    "_source": {
                        "coordinate": {"lat": lat, "lon": lon}
                    },
                }
                
                if "fee" in entry["tags"] and entry["tags"]["fee"] in ("yes", "no"):
                    document["_source"]["fee"] = entry["tags"]["fee"]

                if "wheelchair" in entry["tags"] and entry["tags"]["wheelchair"] in ("yes", "no", "limited", "designated"):
                    document["_source"]["wheelchair"] = entry["tags"]["wheelchair"]

                yield document


for success, info in parallel_bulk(es, get_data(), thread_count=8, queue_size=8):
    if not success:
        print('A document failed:', info)
