"""
Script to repair Costa_Rica
"""
import logging
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString, MultiPolygon, Polygon, Point
from shapely import get_coordinates
from two_line_corner_closure_v3 import making_closure_polygon
from polyTopology_v2 import find_direct_parents, rebuild_with_holes


# pylint: disable=C0301, C0303, W0632, R0914, R0911
logger = logging.getLogger(__name__)


def cut_polygon_to_line(ring, inter_number) ->list[tuple]:
    """
    cut polygon to lines based on sign/x/y change
    ring: valid LinearRing
    inter_number: how many part should be cut
    return: list of [LineString, or Point, or None]
    """
    # need another input: how many lines does it need to be cut 2 or 3 

    # make it list of coords 
    coords = get_coordinates(ring).tolist()

    # find idx where the point has the biggest distance with next point a , b
    # p1 line[:]
    logger.info("Cutting coords based on No of intersection: %d.", inter_number)
    all_xy = list(coords)
    arr = np.array(all_xy)
    next_arr = np.roll(arr, -1, axis=0)
    diff = next_arr - arr
    dist = np.linalg.norm(diff, axis=1)
    top_idx = np.argsort(dist)[-inter_number:][::-1]
    top_idx_sorted = np.sort(top_idx)
    logger.info ("max change index: %s", top_idx_sorted)

    # result is a list of list of separated coords
    result = []
    start = 0
    for idx in top_idx_sorted:
        result.append(coords[start:idx+1])
        start = idx + 1
    result.append(coords[start:])
    logger.info("len of list of cutted lines: %s", len(result))

    # use build part function to reorganize list of coords to 
    if len(result) == 3:
        p1, p2, p3 = result
        line_1 = p2
        line_2 = p3+p1
        result_1 = None
        result_2 = None
        if len(line_1) > 1:
            result_1 = LineString(line_1)
        elif len(line_1) == 1:
            result_1 = Point(line_1)

        if len(line_2) > 1:
            result_2 = LineString(line_2)
        elif len(line_2) == 1:
            result_2 = Point(line_2)

        return [result_1, result_2]
    
    if len(result) == 4:
        p1, p2, p3, p4 = result
        line_1 = p2
        line_2 = p3
        line_3 = p4+ p1
        return [LineString(line_1), LineString(line_2),LineString(line_3)]
    
    if len(result) == 5:
        p1, p2, p3, p4, p5 = result
        line_1 = p2
        line_2 = p3
        line_3 = p4
        line_4 = p5+ p1
        return [LineString(line_1), LineString(line_2),LineString(line_3), LineString(line_4)]
    
    if len(result) == 6:
        p1, p2, p3, p4, p5, p6 = result
        line_1 = p2
        line_2 = p3
        line_3 = p4
        line_4 = p5
        line_5 = p6+ p1
        return [LineString(line_1), LineString(line_2),LineString(line_3), LineString(line_4), LineString(line_5)]
    
    logger.error("cutting line based one distance change error, double check")
    return False
   

def remake_polygon_for_ring(ring, inter_number):
    """
    cut line and make closure for each
    input: ring
    output: MultiPolygon/ False
    """
    
    result = cut_polygon_to_line(ring, inter_number)
    if result is False:
        logger.error("Cut failed")
        return False
    
    if len(result) == 1:
        logger.info("No cut needed, keep original ring")
        return Polygon(ring)
    
    if len(result) == 2:
        logger.info("remake polygon based on two linearline")
        result_1 = result[0]
        result_2 = result[1]
        poly_1 = None
        poly_2 = None
        if isinstance(result_1, LineString):
            poly_1 = making_closure_polygon(result_1)
        else:
            poly_1 = None
        if isinstance(result_2, LineString):
            poly_2 = making_closure_polygon(result_2)
        else:
            poly_2 = None
        poly_list = [poly_1, poly_2]
        plot_polygons(poly_list)

        if poly_1 is None and poly_2 is None:
            logger.error("Failed to make closure polygon")
            return False
        elif poly_1 is not None and poly_2 is not None:
            mp = MultiPolygon([poly_1, poly_2])
            return mp
        elif poly_1 is None and poly_2 is not None:
            return Polygon(poly_1)
        elif poly_1 is not None and poly_2 is None:
            return Polygon(poly_2)

    if len(result) == 3:
        logger.info("remake polygon based on three linearline")
        line_1 = result[0]
        line_2 = result[1]
        line_3 = result[2]
        poly_1 = making_closure_polygon(line_1)
        poly_2 = making_closure_polygon(line_2)
        poly_3 = making_closure_polygon(line_3)
        if poly_1 is False or poly_2 is False or poly_3 is False:
            logger.error("Failed to make closure polygon")
            return False

        ## check topology relations
        poly_list = [poly_1, poly_2, poly_3]
        plot_polygons(poly_list)
        parent, depth = find_direct_parents(poly_list)
        print (f"parent is: {parent}, depth is {depth}")
        result = rebuild_with_holes(poly_list, parent, depth)
        
        mp = MultiPolygon(list(result))
        return mp

    logger.error("Unexpected cut result length: %s", len(result))
    return False


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
