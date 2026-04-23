"""
Script to repair linestring
"""
import logging
import numpy as np
# import matplotlib.pyplot as plt
from shapely.geometry import LineString, MultiLineString
from shapely import get_coordinates

# pylint: disable=C0301, C0303, W0632, R0914, R0911
logger = logging.getLogger(__name__)

def cut_line_to_parts(line, inter_number) ->list[tuple]:
    """
    1. get cut line to lines based on inter_number change
    2. line: LineString shapely object
    3. inter_number: how many part should be cut, int
    4. return: list of coords; length of the list should equal to the (inter_number +1)
    """
    # inter_number should > 0 
    if inter_number < 1:
        raise ValueError("Intersection number need > 0")
 
    # make it list of coords 
    coords = get_coordinates(line).tolist()

    # find idx where the point has the biggest distance with next point a , b
    # p1 line[:]
    logger.info("Cutting line coords based on No: %d of intersection point.", inter_number)
    all_xy = list(coords)
    arr = np.array(all_xy)
    next_arr = np.roll(arr, -1, axis=0)
    diff = next_arr - arr
    dist = np.linalg.norm(diff, axis=1)
    inter_number_int = int(inter_number)
    top_idx = np.argsort(dist)[-inter_number_int:][::-1]
    top_idx_sorted = np.sort(top_idx)
    logger.info ("max change index: %s", top_idx_sorted)

    # result is separted -> a list of list of separated coords
    result = []
    start = 0
    for idx in top_idx_sorted:
        result.append(coords[start:idx+1])
        start = idx + 1
    result.append(coords[start:])
    
    return result

def export_line(line_seperated):
    """
    1. take separated parts of line
    2. check if each part has more than one coords
    3. save and make valid line
    4. return a list of LineString
    """
    
    final_line_sep = []
    for part in line_seperated:
        if len(part) == 1:
            continue
        if len(part) < 1:
            logger.error("Cut Ring Error. Skipped")
            continue
        final_line_sep.append(LineString(part))
    logger.info("Finished cut. Number of valid lines: %s", len(final_line_sep))
    return final_line_sep

def remake_line(geom, inter_number):
    line_sep = cut_line_to_parts(geom, inter_number)
    final_line_list= export_line(line_sep)
    if len(final_line_list)>1:
        return MultiLineString(final_line_list)
    if len(final_line_list) == 1:
        return final_line_list[0]

    return None
