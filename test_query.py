from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('intfloat/e5-large-v2', device="cpu")

INDEX_NAME = "addresses"

es = Elasticsearch("http://127.0.0.1:9200")

embedded_query = model.encode("65 petite rue neuve Dagneux")

response = es.search(index=INDEX_NAME, 
  fields=["label", "coordinates"],
  knn={
    "field": "embedding",
    "query_vector": embedded_query,
    "k": 10,
    "num_candidates": 100
  })

print(len(response["hits"]["hits"]))
