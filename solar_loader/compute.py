import logging
import math
import os
from collections import deque, namedtuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import partial
from time import perf_counter

import numpy as np
from django.conf import settings
from psycopg2.extensions import AsIs
from pytz import timezone
from shapely import affinity, geometry, wkb, wkt, ops

from .geom import (GeometryMissingDimension, get_flattening_mat,
                   multipoly_bbox, tesselate, transform_multipolygon,
                   transform_triangle, unit_vector, vec3_add)
from .gis_geom import GISTriangle
from .lingua import (make_polyhedral, make_polyhedral_p, rows_with_geom,
                     shape_to_feature, triangle_to_geojson)
from .radiation import compute_gk
from .records import Triangle
from .sunpos import get_coords_from_angles

logger = logging.getLogger(__name__)


def get_exposed_area(gis_triangle, sunvec, row_intersect):
    try:
        flat_mat = get_flattening_mat(sunvec)
    except GeometryMissingDimension:
        return gis_triangle.area

    flat_triangle = transform_triangle(flat_mat, gis_triangle.geom)

    triangle_2d = geometry.Polygon([
        flat_triangle.a[:2],
        flat_triangle.b[:2],
        flat_triangle.c[:2],
        flat_triangle.a[:2],
    ])

    intersection = []

    for row in row_intersect:
        # get the geometry
        solid = row[1]
        # apply same transformation than the flatten triangle
        flatten_solid = transform_multipolygon(flat_mat, solid)
        # drops its z
        # solid_2d, zs = multipolygon_drop_z(flatten_solid)
        for s in flatten_solid:
            try:
                it = triangle_2d.intersection(s)
                # if intersection is None:
                #     intersection = it
                # el
                if it.geom_type == 'Polygon':
                    intersection.append(it)  # intersection.union(it)
            except Exception as exc:
                logger.debug(str(exc))

    if len(intersection) == 0:
        return gis_triangle.area
    else:
        # print('R: {} {:.2f} {:.2f}'.format(
        #     len(row_intersect), intersection.area, triangle_2d.area))
        int_area = ops.cascaded_union(intersection).area
        return gis_triangle.area - (
            int_area * gis_triangle.area / triangle_2d.area)
