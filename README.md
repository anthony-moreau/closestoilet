# Closestoilet
A (work-in-progress) web app to help you find the closest public toilet based on Openstreetmap data. The Openstreetmap dataset is free and opensource. On top of mapping data it also contains very detailed information about building, shops and public toilets. Unfortunately, this isn't searchable through the official website (https://www.openstreetmap.org). The objective is to make it searchable in an efficient way. I'm only focusing on toilets but the same process could be used to find shops, public buildings and more.

# Extract list of toilet from openstreetmap

Public toilet data are extracted from openstreetmap data. Go to https://download.geofabrik.de/ and download the desired .osm.pbf file. Then download the pbf2json tool (https://github.com/pelias/pbf2json).

Command line to use to extract the toilet info:

Linux

```
./pbf2json.linux-x64 -tags="amenity~toilets" ./europe-latest.osm.pbf > eu_toilets.json
```

PowerShell

```
.\pbf2json.exe -tags="amenity~toilets" .\europe-latest.osm.pbf | Out-File -FilePath .\eu_toilets.json
```
