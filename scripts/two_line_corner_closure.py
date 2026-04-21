"workable version of creating polygon from one line with one segment"
#pylint: disable=C0303
import logging 
from shapely import LineString, Polygon, Point
from shapely import get_coordinates
#pylint: disable = C0301, C0303, W0632

logger = logging.getLogger(__name__)

# Constant generate from get_bound_seg.py
N_SEG = LineString ([[-16691491, 16691491], [16691491, 16691491]])
S_SEG = LineString ([[-16691491, -16691491], [16691491, -16691491]])
W_SEG = LineString ([[-16691491, -16691491], [-16691491, 16691491]])
E_SEG = LineString ([[16691491, -16691491], [16691491, 16691491]])

# rough corner Point coords 
NW_COR = Point([-16691491, 16691491])
NE_COR = Point([16691491, 16691491])
SW_COR = Point([-16691491, -16691491])
SE_COR = Point([16691491, -16691491])

def build_extended_line(p1, p2, factor = 10):
    """
    make a line p2->p1 
    """
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]

    start = tuple(p2)
    end = (p2[0] + dx*factor, p2[1] + dy * factor)

    result_line = LineString([start, end])
    return result_line

def get_intersection_point(bound_line, test_line):
    """
    return intersection point
    if result if multipoint/linestring/geometrycollection
    """
    inter = bound_line.intersection(test_line)
    if inter.is_empty:
        #logger.error("Intersection: Empty.")
        return False
    
    if inter.geom_type == "Point":
        # logger.info("Intersection: Single Point")
        return inter
    
    if inter.geom_type == "MultiPoint":
        # logger.info("Intersection: Multi Points")
        return list(inter.geoms)[0]
    
    # if geometry collection return geometry
    return inter 

def search_intersection_from_one_side(line_base, bound_line, direction, factor = 10):
    """
    line_base, bound_line: shapely linestring object
    return when find the first intersection 
    return false when find no interesction
    * line base: should be a multistring - has two or more coords
    """
    # logger.info("Search interseciton point for one side: %s", direction)
    coords = get_coordinates(line_base).tolist()
    n = len(coords)

    if n < 2:
        logger.warning("line_base have less than two points")
        return False 
    
    half = n // 2
    if direction == "start":
        for i in range(half):
            p1 = coords[i]
            p2 = coords[i+1]
            test_line = build_extended_line(p1,p2, factor = factor)
            inter = get_intersection_point(bound_line, test_line)

            if inter is not False:
                # logger.info("Find intersection for line_base and seg_bound,extend direction: %s", direction)
                return inter
            
    elif direction == "end":
        for i in range(n-1, half-1, -1):
            if i - 1<0:
                break
            p1 = coords[i]
            p2 = coords[i-1]

            test_line = build_extended_line(p1, p2, factor = factor)
            inter = get_intersection_point(bound_line, test_line)

            if inter is not False:
                # logger.info("Find intersection for line_base and seg_bound; extend direction: %s", direction)
                return inter 
            
    else: 
        raise ValueError("direction must be start or end")
    
    #logger.error("Find inersection from one side fails; recheck premeter")
    return False


def making_closure_polygon(line_base):
    """
    Main workflow for making closure polyon
    line_base.prem: Multiline - shapely object
    bound_seg: Line - shapely object (only two points segment)
    """
    # logger.info("Attempting to enclosure line and segment")
    # find intersection point on which boundary 
    start_hits = {}
    end_hits = {}

    for name, boundary in [
        ("East", E_SEG),
        ("South", S_SEG),
        ("West", W_SEG),
        ("North", N_SEG),
    ]:  
        start_intersection = search_intersection_from_one_side(line_base, boundary, "start")
        if start_intersection is not False:
            #logger.info ("start extend line intersect with %s boundary", name)
            start_hits[name] = start_intersection

        end_intersection = search_intersection_from_one_side(line_base, boundary, "end")
        if end_intersection is not False:
            #logger.info ("end extend line intersect with %s boundary", name)
            end_hits[name] = end_intersection
        
    # expected result: only one inter find for each line
    if len(start_hits) == 1 and len(end_hits) == 1:
        
        # if start and end intersection are on the same boundary
        start_name, start_point = next(iter(start_hits.items()))
        end_name, end_point = next(iter(end_hits.items()))
        if start_name == end_name:
            #logger.info("This line has two inter on one boundary")
            poly = make_poly_with_one_boundary(start_point, end_point, line_base)
            return poly
        
        # if start and end interection are on different boundary 
        if start_name != end_name:
            #logger.info("This line has two inter on two different boundaries")
            combine = [start_name, end_name]
            if combine in [['North','South'], ['South', 'North'], ['East', 'West'], ['West', 'East']]:
                logger.warning("But different boundaries are in opposite direction")
                return False
            corner = find_corner_point(combine)
            poly = make_poly_with_corner(start_point, end_point, line_base, corner)
            return poly

    return False


def make_poly_with_one_boundary(start_intersection, end_intersection, line_base):
    """
    Method: connect start_point -> line -> end_point
    Return Shapely Polygon
    """
    coords = []
    if start_intersection is False:
        logger.warning ("Extending start half of line can not find intersection with bound line")
        return False
    
    coords.append(start_intersection.coords[0])

    for l in line_base.coords:
        coords.append(l)

    if end_intersection is False:
        logger.warning ("Extending end half of line can not find intersection with bound line")
        return False
    
    coords.append(end_intersection.coords[0])

    final_poly = Polygon(coords)
    return final_poly


def find_corner_point(combine):
    """
    Return shapely point object
    """
    if combine in [['North', 'West'], ['West', 'North']]:
        corner = NW_COR
    elif combine in [['North', 'East'], ['East', 'North']]:
        corner = NE_COR
    elif combine in [['South', 'East'], ['East', 'South']]:
        corner = SE_COR
    elif combine in [['South', 'West'], ['West', 'South']]:
        corner = SW_COR
    else:
        logger.warning("Somethign wrong find conner point")
        return False

    return corner


# def validate_candidate_polygon(poly):
#     if poly is False:
#         return False
#     if poly.is_empty:
#         return Falase


def make_poly_with_corner(start_intersection, end_intersection, line_base, corner):
    """
    make poly: start_point -> baseline -> end_point -> corner
    """
    coords = []
    if start_intersection is False:
        logger.warning ("Extending start half of line can not find intersection with bound line")
        return False
    
    coords.append(start_intersection.coords[0])

    for l in line_base.coords:
        coords.append(l)

    if end_intersection is False:
        logger.warning ("Extending end half of line can not find intersection with bound line")
        return False
    
    coords.append(end_intersection.coords[0])
    coords.append(corner.coords[0])
    final_poly = Polygon(coords)
    return final_poly
