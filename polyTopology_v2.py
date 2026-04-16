"""
Script to figure the topology relation of a set of polygon
developed from version 1
only using difference - skip testing share edge or not 
"""
import logging
from shapely import STRtree, make_valid
from shapely.geometry import Polygon, MultiPolygon

# pylint: disable=C0301, C0303, W0632, R0914, R0911, C0200
logger = logging.getLogger(__name__)
 
def check_valid(polygons):
    """
    bounce back if there is invalid geom in the list 
    """
    for geom in polygons:
        if not geom.is_valid:
            logger.error("list has invlid geom")
            return False
    return True


def find_direct_parents(polygons):
    """
    polygons: list[Polygon]

    return:
        parent: 每个 polygon 的直接父级索引，没有则为 None
        depth: 每个 polygon 的嵌套深度
    """

    if check_valid(polygons) is False:
        return [None], [None]
    
    tree = STRtree(polygons)
    parent = [None] * len(polygons)
    #share_edge_pairs = set()

    for i, child in enumerate(polygons):
        candidate_idx = tree.query(child)
        possible_parents = []
        for j in candidate_idx:
            j = int(j)
            if i == j:
                continue
         
            candidate = polygons[j]

            if candidate.area <= child.area:
                continue

            if candidate.covers(child):
                possible_parents.append(j)
        
        if possible_parents:
            # 选“最小的那个包含者”作为直接父级
            p = min(possible_parents, key = lambda j: polygons[j].area)
            parent[i] = p

            # share = polygons[p].boundary.intersection(child.boundary)
            # if share.geom_type in ("LineString", "MultiLineString"):
            #     if not share.is_empty:
            #         share_edge_pairs.add((p,i))

    depth = compute_depth(parent)
    return parent, depth


def compute_depth(parent):
    """根据 parent 数组计算嵌套深度。"""
    depth = [0] * len(parent)

    for i in range(len(parent)):
        d = 0
        cur = parent[i]
        while cur is not None:
            d += 1
            cur = parent[cur]
        depth[i] = d
    return depth


def rebuild_with_holes(polygons, parent, depth):
    """
    Making polygon/multipolygon with topology
    polygons: list of valid polygon
    return: list of nested polygon
    """
    if all(x is None for x in parent):
        logger.info("There no hole in provided polygon list; return original polygon list")
        return polygons
    
    children = [[] for _ in range (len(polygons))]
    for i, p in enumerate (parent):
        #i 实际上是每个polygon的代号
        #p 实际上是直接父polygon的代号
        # childeren 保存每个父poly的直接子poly是哪些
        if p is not None:
            children[p].append(i)

    result = []
    for i, poly in enumerate(polygons):
        # 偶数层作为实体 shell
        if depth[i] % 2 != 0:
            continue

        # 当前 shell 的工作几何
        shell_geom = poly

        for child_idx in children[i]:
            if depth[child_idx] % 2 != 1:
                continue

            child_poly = polygons[child_idx]
            shell_geom = shell_geom.difference(child_poly)

            if not shell_geom.is_valid:
                shell_geom = make_valid(shell_geom)
            if shell_geom.is_empty:
                break
        if shell_geom.is_empty:
            continue

        if isinstance(shell_geom, Polygon):
            result.append(shell_geom)

        elif isinstance(shell_geom, MultiPolygon):
            result.extend([part for part in shell_geom.geoms if not part.is_empty])

    return result
