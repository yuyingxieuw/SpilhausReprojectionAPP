"""
run experiment code script
"""

import geopandas as gpd
import numpy as np

from shapely.geometry import Polygon, LinearRing, LineString
from shapely.plotting import plot_polygon, plot_points
import matplotlib.pyplot as plt
bound_4326 = gpd.read_file("data/bound_merge_4326.geojson")
bound = bound_4326.geometry.iloc[0]
print(bound.geom_type)
gdf = gpd.read_file("data/spain4326.geojson")
gdf_exploded = gdf.explode(index_parts=True, ignore_index=True)
print(gdf_exploded)
poly = gdf_exploded.loc[17].geometry
poly_coords = np.array(poly.exterior.coords)
ring_spain = LinearRing(poly_coords)

def to_360(ring):
        # turn 
        new_coords = []
        coords = list(ring.coords)
        for lon, lat in coords:
            lon_new = lon if lon >= 0 else lon + 360
            new_coords.append((lon_new, lat))
        return LinearRing(new_coords)

spain_360 = to_360(ring_spain)
# spain_360_poly = Polygon(spain_360.coords)
# spain_360_valid = shapely.make_valid(spain_360_poly)
# plot_polygon(spain_360_poly, color="blue")
# _, ax = plt.subplots()
# x,y = ring_spain.xy
# ax.plot(x,y)
# x1,y1 = bound.xy
# ax.plot(x1,y1)
# plt.show()
meridian_0 = LineString([(0, -90),(0, 90)])
result = ring_spain.intersects(meridian_0)
print(result)
