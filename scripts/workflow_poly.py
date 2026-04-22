"""
Script to manage workflow process polygon repair 
"""
import logging
import geopandas as gpd
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, LinearRing, MultiPolygon, LineString
from shapely.ops import transform, unary_union
from scripts.logging_config import setup_logger
from scripts.repair_ring import remake_polygon_for_ring

# pylint: disable=C0301, C0303, W0632, R0914, R0911, R0912, R0915, W0718, W0108
setup_logger()
logger = logging.getLogger(__name__)

def get_inital_polygon(data):
    """
    1. turn geojson data to geopands file
    2. check validation of each feature
    3. return false if there's any invalid geometry
    4. double check crs; if minnot 4326 make it 4326
    """
    logger.debug("Parsing origional file../")
    #gdf = gpd.read_file(in_path)
    if data["type"] == "FeatureCollection":
        gdf = gpd.GeoDataFrame.from_features(data["features"])
    elif data["type"] == "Feature":
        gdf = gpd.GeoDataFrame.from_features([data])
    else:
        raise ValueError("Input must be a GeoJSON Feature or FeatureCollection")

    #check validataion
    for geom in gdf.geometry:
        if not geom.is_valid:
            logger.error("List has invalid geom.")
            return False
        
    #double check CRS
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    logger.info("Passed validation check; CRS set to EPSG:4326")
    return gdf

def portrait (gdf):
    """
    1. explode multipolygon if it is
    2. extract exterior and interior
    """
    # explode 
    gdf_exploded = gdf.explode(index_parts=False)

    # add exterior column -> LinearRing
    # add interior column -> list[LinearRing] or []
    gdf_exploded["has_interior"] = gdf_exploded.geometry.apply(lambda geom: len(geom.interiors) > 0 )
    gdf_exploded["exterior"] = gdf_exploded.geometry.apply(lambda geom: geom.exterior if geom and geom.geom_type == "Polygon" else [])
    gdf_exploded["interior"] = gdf_exploded.geometry.apply(lambda geom: list(geom.interiors) if geom and geom.geom_type == "Polygon" else [])
    
    return gdf_exploded


def label_inter_number(gdf_exploded):
    """
    1. operate intersection between boundary line and polygon
    2. add column exterior_inter to store exterior inter number
    3. add column interior_inter: [] or [0,1,2,3]
    """
    # the bound has redefine the wrap boundary to [0, 360]
    # so poly across lon 0 remain unchanged incase it acrosses the whole map
    bound_4326 = gpd.read_file("data/bound_merge_4326.geojson")
    bound = bound_4326.geometry.iloc[0]
    meridian_0 = LineString([(0, -90),(0, 90)])
    def to_360(ring):
        # turn 
        if ring.intersects(meridian_0) is True:
            return ring
        new_coords = []
        coords = list(ring.coords)
        for lon, lat in coords:
            lon_new = lon if lon >= 0 else lon + 360
            new_coords.append((lon_new, lat))
        return LinearRing(new_coords)
    
    logger.info("Labeling intersection number for exterior")
    gdf_exploded['exterior_360'] = gdf_exploded["exterior"].apply(to_360)

    def count_intersection_points(candidate_ring):
        intersection_geom = bound.intersection(candidate_ring)
        if intersection_geom.is_empty:
            return 0
        
        if intersection_geom.geom_type =="Point":
            return 1
        
        if intersection_geom.geom_type == "MultiPoint":
            return len(intersection_geom.geoms)
        
        if intersection_geom.geom_type in ("LineString", "MultiLineString"):
            return 0
        
        if intersection_geom.geom_type == 'GeometryCollection':
            count = 0
            for g in intersection_geom.geoms:
                if g.geom_type == "Point":
                    count += 1
                elif g.geom_type == "MultiPoint":
                    count += len(g.geoms)
            return count

        return 0
    
    gdf_exploded['exterior_inter'] = gdf_exploded["exterior_360"].apply(count_intersection_points)

    ## for interior 
    def to_360_interior(ring_list):
        if not ring_list:
            return []
        results_360 = []
        for ring in ring_list:
            result = to_360(ring)
            results_360.append(result)
        return results_360
    
    def count_intersection_points_for_interior(ring_list):
        if not ring_list:
            return []
        results = []
        for ring in ring_list:
            result = count_intersection_points(ring)
            results.append(result)
        return results
    

    logger.info("Labeling intersection number for interiors")
    gdf_exploded['interior_360'] = gdf_exploded["interior"].apply(to_360_interior)
    gdf_exploded["interior_inter"] = gdf_exploded["interior_360"].apply(count_intersection_points_for_interior)

    drop_column = ['exterior_360','interior_360']
    gdf_inter = gdf_exploded.drop(drop_column, axis=1)
    
    def report(result):
        print(result)
        has_interior = result.index[result['has_interior']]
        has_interior_list = has_interior.tolist() # e.g.[0,0,5,45....]
        print ("---------index(level-0) of polygon has interior----------")
        print(has_interior_list)

        exterior_has_inter = result.index[result['exterior_inter']>0].tolist()
        print("-----------Exterior has intersection with boundary: Index(level-0) ----------")
        print(exterior_has_inter)

        interior_has_inter = result.index[result['interior_inter'].apply(lambda x: bool(x))].tolist()
        print("-----------Interior has intersection with boundary: Index(level-0) ----------")
        print(interior_has_inter)
        
        # exterior_has_inter_df = result[result['exterior_inter']>0]
        # exterior_has_inter_df=exterior_has_inter_df.drop(columns=['exterior'])
        # exterior_has_inter_df.to_file("ExteriorInter.geojson", driver = "GeoJSON")
        
    report(gdf_inter)

    return gdf_inter 
    

def change_crs(ring):
    """
    change polygon to 54099
    ring is a LinearRing (exterior) or List of LinearRing (hole)
    """
    crs_54099 = CRS.from_proj4("+proj=spilhaus +lat_0=-49.56371678 +lon_0=66.94970198 +azi=40.17823482 +k_0=1.4142135623731 +rot=45 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs +type=crs")
    crs_4326 = CRS.from_epsg(4326)
    tform = Transformer.from_crs(crs_4326, crs_54099, always_xy = True).transform
    
    if isinstance(ring, LinearRing):
        return transform(tform, ring)
    
    if isinstance(ring, list):
        if ring:
            logger.info("Changing CRS for interior")
            ring_54099_list = []
            for ring_item in ring:
                ring_54099 = transform(tform, ring_item)
                ring_54099_list.append(ring_54099)
            return ring_54099_list
        return ring
    
    logger.error ("change crs failed, input ring is not LinearRing or a list of LinearRing")
    return None


def repair_geodataframe(gdf):
    """
    1. take a gdf with exterior/interior_54099 and inter number column 
    2. run repair script (take Ring get MultiPolygon or Polygon)
    3. return valid repaired geodataframe
    """
    
    geom_repaired = []
    repaired_exterior = 0
    repaired_interior = 0

    for _, row in gdf.iterrows():
        # deal with exterior
        final_exterior = None
        ex_inter_number = row["exterior_inter"]
        exterior_ring = row["exterior_54099"]
        if ex_inter_number == 0:
            final_exterior = Polygon(exterior_ring)

        elif ex_inter_number != 0:
            # _, ax = plt.subplots()
            # x,y = exterior_ring.xy
            # ax.plot(x,y)
            # plt.show()
            fixed_exterior = remake_polygon_for_ring(exterior_ring, ex_inter_number)
            if fixed_exterior:
                logger.info("Repaired one exterior")
                repaired_exterior +=1
            else:
                logger.error("Recheck exterior ring; Failed to cut. Put None")
            final_exterior = fixed_exterior

        # deal with interior
        has_interior = row["has_interior"]
        if has_interior is False:
            geom_repaired.append(final_exterior)

        elif has_interior is True:
            fixed_hole_list = []
            interior_ring_list = row["interior_54099"]
            in_inter_number_list = row["interior_inter"]
            for i, interior_ring in enumerate(interior_ring_list):
                in_inter_number = in_inter_number_list [i]
                if in_inter_number !=0:
                    fixed_hole = remake_polygon_for_ring(interior_ring, in_inter_number)
                    if fixed_hole:
                        repaired_interior += 0
                    fixed_hole_list.append(Polygon(fixed_hole))
                elif in_inter_number == 0:
                    fixed_hole_list.append(interior_ring)

            holes_union = unary_union(fixed_hole_list)
            
            if final_exterior is not None:
                geom_repaired.append(final_exterior.difference(holes_union))
            else:
                geom_repaired.append(None)
                     
    gdf = gdf.copy()
    gdf["repaired_geom"] = geom_repaired

    # clean data
    column_drop = ['geometry','has_interior','exterior_inter', 'interior_inter', 'exterior_54099', 'interior_54099', 'exterior', 'interior']
    gdf_processed = gdf.drop(column_drop, axis=1, errors="ignore")
    gdf_processed = gdf_processed.set_geometry('repaired_geom')

    #print report
    print ("-----------Repaired Exterior----------")
    print (repaired_exterior)
    print ("-----------Repaired Interior----------")
    print (repaired_interior)
    return gdf_processed

def regroup_to_multipolygon(gdf_processed):
    """
    1. regroup polygon to multi-polygon based original index
    """
    
    def geom_to_polys(geom):
        if geom is None or geom.is_empty:
            return []
        if geom.geom_type == "Polygon":
            return [geom]
        if geom.geom_type == "MultiPolygon":
            return list(geom.geoms)
        return []
    
    def collect(geoms):
        polys = []
        for geom in geoms:
            polys.extend(geom_to_polys(geom))
        if not polys:
            return None
        if len(polys) == 1:
            return polys[0]
        return MultiPolygon(polys)

    attrs = gdf_processed.drop(columns = 'repaired_geom').groupby(level=0).first()
    geom = gdf_processed.groupby(level=0)['repaired_geom'].apply(collect)

    gdf_final = gpd.GeoDataFrame(attrs, geometry=geom, crs = "ESRI:54099")
    return gdf_final

def run_program(geojson_data):
    """
    main workflow
    """
    
    gdf = get_inital_polygon(geojson_data)

    if gdf is False:
        logger.error ("Making dataframe fail, double check data validation")
        return False
    
    # explode multipolygon to polyton
    gdf_exploded = portrait(gdf)

    # check each polgyon; label inter number with boundary 
    gdf_inter_label = label_inter_number(gdf_exploded)

    # change CRS to 54099
    gdf_inter_label["exterior_54099"] = gdf_inter_label["exterior"].apply(change_crs)
    gdf_inter_label["interior_54099"] = gdf_inter_label["interior"].apply(change_crs)

    # check if need repair
    gdf_processed = repair_geodataframe(gdf_inter_label)
    # print(gdf_processed.columns.to_list())

    result = regroup_to_multipolygon(gdf_processed)
    # print(result)
    # export result
    # result.to_file("Fixed_world.geojson", driver = "GeoJSON")
    logger.info("Data Transform Finished")
    return result.to_json()
    

# if __name__ == "__main__":
#     run_program(geojson_data) 
