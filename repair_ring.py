"""
Script to repair ring
"""
import logging
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely import get_coordinates
from two_line_corner_closure_v3 import making_closure_polygon
from polyTopology_v2 import find_direct_parents, rebuild_with_holes


# pylint: disable=C0301, C0303, W0632, R0914, R0911
logger = logging.getLogger(__name__)


def cut_ring_to_parts(ring, inter_number) ->list[tuple]:
    """
    1. get cut polygon to lines based on sign/x/y change
    2. ring: valid LinearRing
    3. inter_number: how many part should be cut, int
    4. return: list of coords; length of the list should equal to the (inter_number +1)
    Note:
    1. should take a valid linear ring(must have a minimum of 4 coordinate tuples)
    """
    # inter_number should > 0 
    if inter_number < 1:
        raise ValueError("Intersection number need > 0")
 
    # make it list of coords 
    coords = get_coordinates(ring).tolist()

    # find idx where the point has the biggest distance with next point a , b
    # p1 line[:]
    logger.info("Cutting coords based on No%d of intersection point.", inter_number)
    all_xy = list(coords)
    arr = np.array(all_xy)
    next_arr = np.roll(arr, -1, axis=0)
    diff = next_arr - arr
    dist = np.linalg.norm(diff, axis=1)
    top_idx = np.argsort(dist)[-inter_number:][::-1]
    top_idx_sorted = np.sort(top_idx)
    logger.info ("max change index: %s", top_idx_sorted)

    # result is separted ring -> a list of list of separated coords
    result = []
    start = 0
    for idx in top_idx_sorted:
        result.append(coords[start:idx+1])
        start = idx + 1
    result.append(coords[start:])
    
    return result



def ring_parts_to_linestring(ring_seprated):
    """
    1. take seprated part of rings
    2. reorgnize coords based on sequence
    eg: p1, p2, p3 -> p2, p3+p1
    3. drop Point, only save LineString(At least 2 coordinate tuples)
    4. return list of shapely object: [LineString, LineString, ...] or []
    """
    # double check result
    if len(ring_seprated) <2:
        logger.error("Cut Ring Error.")
        return []
    
    # reorgnize coords
    p1= ring_seprated[0]
    new_ring_sep = list(ring_seprated[1:])
    new_ring_sep[-1] = new_ring_sep[-1]+p1
    
    # drop Point and export LineString
    final_ring_sep = []
    for part in new_ring_sep:
        if len(part) == 1:
            continue
        if len(part) < 1:
            logger.error("Cut Ring Error.")
            continue
        final_ring_sep.append(LineString(part))

    logger.info("Finished cut. Number of valid lines: %s", len(final_ring_sep))
    return final_ring_sep
   


def remake_polygon_for_ring(ring, inter_number):
    """
    main workflow function
    1. take a valid ring and cut_ring_to_parts
    2. run ring_parts_to_linestring
    3. run remake polygon for linestring
    4. return multipolygon or polygon or none
    """
    
    ring_sep = cut_ring_to_parts(ring, inter_number)
    result = ring_parts_to_linestring(ring_sep)

    # nothing in cutted line list
    if not result:
        logger.info("Error in cuting ring (might be just points). Nothing returns.")
        return None
    
    # line -> polygon
    make_poly_list = []
    for line in result:
        poly = making_closure_polygon(line)
        if poly is False:
            continue
        if not poly.is_valid:
            continue
        make_poly_list.append(poly)
    logger.info("Number of generated poly through cutted lines %s:", len(make_poly_list))

    ## check topology relations
    #plot_polygons(make_poly_list)
    if len(make_poly_list) > 1:
        parent, depth = find_direct_parents(make_poly_list)
        if any(parent):
            print (f"parent is: {parent}, depth is {depth}")
            result = rebuild_with_holes(make_poly_list, parent, depth)
            logger.info("Return fixed multiPolygon")
            return MultiPolygon(list(result))

    if len(make_poly_list) == 1:
        logger.info("Return fixed Polygon")
        return Polygon(make_poly_list)
    
    return None


def plot_polygons(polygons):
    """
    Plot to check holes 
    For debug, add plot if you want
    """
    _, ax = plt.subplots()

    for poly in polygons:
        if (poly is None) or (poly is False):
            continue
        x, y = poly.exterior.xy
        ax.plot(x, y)

        # 如果有 holes，也一起画出来
        for interior in poly.interiors:
            hx, hy = interior.xy
            ax.plot(hx, hy)

    ax.set_aspect("equal")
    plt.show()
