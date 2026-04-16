"""
run experiment code script
"""

import geopandas as gpd
from shapely.geometry import Polygon
from shapely.plotting import plot_polygon
import matplotlib.pyplot as plt

gdf = gpd.read_file("data/China4326.geojson")
gdf_exploded = gdf.explode(index_parts=True, ignore_index=True)
print(gdf_exploded)

gdf_exploded['somevalue'] = gdf_exploded.index


result = gdf_exploded[gdf_exploded['somevalue']==4]
print(result)
result.to_file("test.geojson", driver="GeoJSON")
coord= [
            [120.606781444088767, 37.979885154559952],
            [120.625824479885509, 37.972561056811216],
            [120.622894766371417, 37.948797989958223],
            [120.606781444088767, 37.979885154559952]
          ]
        
poly = Polygon(coord)
print(poly.is_valid)
plot_polygon(poly, color='blue', alpha=0.5)
plt.show()


# deal with hole
        # interior_54099_list = row["interior_54099"]
        
        # if interior_54099_list:
        #     logger.info("This geom has interior. Fixing")
        #     interior_inter_list = row["interior_inter"]
        #     exterior_has_hole = fixed_exterior

        #     for i, interior in enumerate(interior_54099_list):
        #         interior_inter_number = interior_inter_list[i]
        #         if interior_inter_number != 0:
        #             fixed_hole = remake_polygon_for_ring(interior, interior_inter_number)
        #             if fixed_hole is not False:
        #                 exterior_has_hole = exterior_has_hole.difference(fixed_hole)
        #     final_exterior = exterior_has_hole

        #     merged_repaired_geom = unary_union([g for g in repaired_geoms if g is not None])
