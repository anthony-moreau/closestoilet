from elasticsearch import Elasticsearch

INDEX_NAME = "toilets"

es = Elasticsearch("http://127.0.0.1:9200")

response = es.search(index=INDEX_NAME, query={
    "bool": {
      "must": {
        "match_all": {}
      },
      "filter": {
        "geo_distance": {
          "distance": "200km",
          "coordinate": {
            "lat": 48.8489,
            "lon": 2.2925
          }
        }
      }
    }
  })

print(response)
