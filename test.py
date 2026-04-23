import geopandas as gpd
from pyproj import CRS 
crs_54099 = CRS.from_proj4("+proj=spilhaus +lat_0=-49.56371678 +lon_0=66.94970198 +azi=40.17823482 +k_0=1.4142135623731 +rot=45 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs +type=crs")
data = gpd.read_file("data/world4326.geojson")

data = data.to_crs(crs_54099)
print(data)
data.to_file("data/world54099.geojson", driver="GeoJSON")
