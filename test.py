import geopandas as gpd
import json
from geojson import FeatureCollection
data = {
  "type": "Feature",
  "properties": {
    "name": "small polygon"
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [-122.35, 47.60],
        [-122.35, 47.61],
        [-122.34, 47.61],
        [-122.34, 47.60],
        [-122.35, 47.60]
      ]
    ]
  }
}


if data["type"] == "FeatureCollection":
    gdf = gpd.GeoDataFrame.from_features(data["features"])
elif data["type"] == "Feature":
    gdf = gpd.GeoDataFrame.from_features([data])
else:
    raise ValueError("Input must be a GeoJSON Feature or FeatureCollection")

print(gdf)

d = gdf.to_json()
print(d)
