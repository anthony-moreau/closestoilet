import time

from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from elasticsearch import Elasticsearch
import numpy as np
import plotly.graph_objects as go
from sentence_transformers import SentenceTransformer


TOILET_INDEX_NAME = "toilets"
ADDRESS_INDEX_NAME = "addresses"

model = SentenceTransformer('intfloat/e5-large-v2', device="cpu")

es = Elasticsearch("http://127.0.0.1:9200")

def find_closest_toilets(latitude, longitude):
    query = {
        "bool": {
            "must": {
                "geo_distance": {
                    "distance": "200km",
                    "coordinate" : {
                        "lat": latitude,
                        "lon": longitude
                    }
                }
            },
        }
    }
    sort =  {
        "_geo_distance" : {
            "coordinate" : {
                "lat": latitude,
                "lon": longitude
            },
            "order" : "asc",
            "unit" : "km",
            "mode" : "min",
            "distance_type" : "arc",
            "ignore_unmapped": True
        }
    }
    hits = es.search(index=TOILET_INDEX_NAME, query=query, sort=sort, size=20).body["hits"]["hits"]
    lat = []
    lon = []
    for hit in hits:
        lat.append(hit["_source"]["coordinate"]["lat"])
        lon.append(hit["_source"]["coordinate"]["lon"])
    
    return lat, lon


def find_matching_addresses(query):
    embedded_query = model.encode(query)
    response = es.search(index=ADDRESS_INDEX_NAME, 
        fields=["label", "coordinates"],
        knn={
            "field": "embedding",
            "query_vector": embedded_query,
            "k": 10,
            "num_candidates": 100
        })
    return [to_json_object(doc["_source"]) for doc in response["hits"]["hits"]]


def to_json_object(doc):
    return{
            "label": doc["label"],
            "lat": doc["coordinate"]["lat"],
            "lon": doc["coordinate"]["lon"]
        }


def zoom_center(lons: tuple=None, lats: tuple=None, lonlats: tuple=None,
        format: str='lonlat', projection: str='mercator',
        width_to_height: float=2.0) -> (float, dict):
    """Finds optimal zoom and centering for a plotly mapbox.
    Must be passed (lons & lats) or lonlats.
    Temporary solution awaiting official implementation, see:
    https://github.com/plotly/plotly.js/issues/3434
    
    Parameters
    --------
    lons: tuple, optional, longitude component of each location
    lats: tuple, optional, latitude component of each location
    lonlats: tuple, optional, gps locations
    format: str, specifying the order of longitud and latitude dimensions,
        expected values: 'lonlat' or 'latlon', only used if passed lonlats
    projection: str, only accepting 'mercator' at the moment,
        raises `NotImplementedError` if other is passed
    width_to_height: float, expected ratio of final graph's with to height,
        used to select the constrained axis.
    
    Returns
    --------
    zoom: float, from 1 to 20
    center: dict, gps position with 'lon' and 'lat' keys

    >>> print(zoom_center((-109.031387, -103.385460),
    ...     (25.587101, 31.784620)))
    (5.75, {'lon': -106.208423, 'lat': 28.685861})
    """
    if lons is None and lats is None:
        if isinstance(lonlats, tuple):
            lons, lats = zip(*lonlats)
        else:
            raise ValueError(
                'Must pass lons & lats or lonlats'
            )
    
    maxlon, minlon = max(lons), min(lons)
    maxlat, minlat = max(lats), min(lats)
    center = {
        'lon': round((maxlon + minlon) / 2, 6),
        'lat': round((maxlat + minlat) / 2, 6)
    }
    
    # longitudinal range by zoom level (20 to 1)
    # in degrees, if centered at equator
    lon_zoom_range = np.array([
        0.0007, 0.0014, 0.003, 0.006, 0.012, 0.024, 0.048, 0.096,
        0.192, 0.3712, 0.768, 1.536, 3.072, 6.144, 11.8784, 23.7568,
        47.5136, 98.304, 190.0544, 360.0
    ])
    
    if projection == 'mercator':
        margin = 1.2
        height = (maxlat - minlat) * margin * width_to_height
        width = (maxlon - minlon) * margin
        lon_zoom = np.interp(width , lon_zoom_range, range(20, 0, -1))
        lat_zoom = np.interp(height, lon_zoom_range, range(20, 0, -1))
        zoom = round(min(lon_zoom, lat_zoom), 2)
    else:
        raise NotImplementedError(
            f'{projection} projection is not implemented'
        )
    
    return zoom, center


app = Dash()

app.layout = html.Div([
    html.Div([
        html.H1("Find the closest toilet"),
        html.Div([
            html.Button("Update position", id="toggle-geolocation", n_clicks=0),
            dcc.Interval(id="update-geo-location", interval=30000),
            dcc.Geolocation(id="geolocation"),
            dcc.Input(id="latitude-input", type="number"), 
            dcc.Input(id="longitude-input", type="number"), 
            html.Button("Search", id="search-button", n_clicks=0),
            dcc.Input(id='address-search', type='text', list='list-suggested-addresses', value=''),
            dcc.Store("suggested-addresses"),
            html.Datalist(id='list-suggested-addresses'),
            dcc.Store("latitude"),
            dcc.Store("longitude")
            ])
    ], style={"height": "10%"}),
    html.Div(id="fig-container", style={"display": "inline-block", "width": "100%", "height": "90%"})
], style={"height": "97vh"})


@app.callback(
    Output("suggested-addresses", "data"), 
    Output("list-suggested-addresses", "children"), 
    Input("address-search", "value"),
)
def search_address_index(query):
    start_time = time.time()
    suggestions = find_matching_addresses(query)
    print(time.time() - start_time)
    return suggestions, [html.Option(value=suggestion["label"]) for suggestion in suggestions]


@app.callback(
    Input("list-suggested-addresses", "n_clicks"),
    State("address-search", "value"),
    State("suggested-addresses", "data"), 
)
def accept_suggestion(n_click, selected_address, address_data):
    if n_click > 0:
        print(selected_address)


"""@app.callback(
    Output("geolocation", "update_now"), 
    Input("toggle-geolocation", "n_clicks"),
    Input("update-geo-location", "n_intervals")
)
def update_now(click, interval):
    return True if (click or interval) and (click > 0 or interval > 0) else False"""


@app.callback(
    Output("latitude", "data"), 
    Output("longitude", "data"), 
    Input("geolocation", "position"), 
    Input("latitude-input", "value"),
    Input("longitude-input", "value")
)
def aggregate(position, input_lat, input_lon):
    print(position, input_lat, input_lon)
    if position:
        return position["lat"], position["lon"]
    elif input_lat and input_lon:
        return input_lat, input_lon
    raise PreventUpdate


@app.callback(
    Output("fig-container", "children"),
    Input("search-button", "n_clicks"),
    Input("latitude", "data"),
    Input("longitude", "data"),
)
def search_toilet_index(n_clicks, latitude, longitude):
    if latitude is not None and longitude is not None:
        lat, lon = find_closest_toilets(latitude, longitude)
        zoom, center = zoom_center(lons=lon, lats=lat)
        return dcc.Graph(figure=go.Figure([go.Scattermapbox(lat=lat[:20], lon=lon[:20], marker=go.scattermapbox.Marker(size=20)),
                                           go.Scattermapbox(lat=[latitude], lon=[longitude], marker=go.scattermapbox.Marker(size=20))], 
                                          layout=dict(mapbox_style="open-street-map", 
                                                      margin=dict(b=0, r=0, l=0, t=0),
                                                      mapbox = dict(center = center, zoom = zoom),
                                                      showlegend=False)),
                         style={"width": "100%", "height": "100%"})


if __name__ == "__main__":
    app.run_server(debug=False)