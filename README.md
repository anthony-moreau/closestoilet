# closestoilet
A web app to help you find the closest public toilet

# extract list of toilet from openstreetmap

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
