from collections import defaultdict
import json

possible_tags = defaultdict(lambda: defaultdict(lambda: 0))

with open("eu_toilets.json", "r", encoding="utf-16-le") as source:
    for i, line in enumerate(source):
        entry = json.loads(line.replace("\ufeff", ""))

        for tag in entry["tags"].keys():
            possible_tags[tag][entry["tags"][tag]] += 1

common_tags = [tag for tag in possible_tags.keys() if sum(c for c in possible_tags[tag].values()) > 100]
print("break point here")
