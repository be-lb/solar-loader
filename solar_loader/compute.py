import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial

import numpy as np
from psycopg2.extensions import AsIs
from shapely import geometry, ops
from shapely.geos import TopologicalError

from .geom import (
    GeometryMissingDimension,
    get_flattening_mat,
    get_triangle_area,
    get_triangle_inclination,
    get_triangle_azimut,
    tesselate,
    transform_multipolygon,
    transform_triangle,
    unit_vector,
    translation_matrix,
    multipolygon_drop_z,
)
from .gis_geom import GISTriangle
from .lingua import (
    make_polyhedral,
    rows_with_geom,
    shape_to_feature,
    triangle_to_geojson,
)
from .radiation import compute_gk
from .records import Triangle
from .sunpos import get_sun_position
from .time import TimeCounter, generate_sample_days

logger = logging.getLogger(__name__)


def init_triangle(tim, gis_triangle):
    center = gis_triangle.center
    sunpos = get_sun_position(center, tim)

    triangle_azimuth = gis_triangle.get_azimuth()
    triangle_inclination = gis_triangle.get_inclination()

    triangle_area = gis_triangle.area
    triangle_rdiso = gis_triangle.get_rdiso()
    triangle_rdiso_flat = gis_triangle.get_rdiso_flat()

    return (center, sunpos, triangle_azimuth, triangle_inclination,
            triangle_area, triangle_rdiso, triangle_rdiso_flat)


# def get_intersections_for_triangle(gis_triangle, sunvec, db):
#     sunvecunit = unit_vector(sunvec)

#     nearvec = sunvecunit * 1.0  # 0.1
#     farvec = sunvecunit * 200.0

#     triangle_near = Triangle(gis_triangle.geom.a + nearvec,
#                              gis_triangle.geom.b + nearvec,
#                              gis_triangle.geom.c + nearvec)
#     triangle_far = Triangle(gis_triangle.geom.a + farvec,
#                             gis_triangle.geom.b + farvec,
#                             gis_triangle.geom.c + farvec)
#     polyhedr = make_polyhedral(triangle_near, triangle_far)

#     return list(rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ), 1))

# def get_exposed_area_bak(gis_triangle, sunvec, row_intersect):
#     try:
#         flat_mat = get_flattening_mat(sunvec)
#     except GeometryMissingDimension:
#         return gis_triangle.area

#     flat_triangle = transform_triangle(flat_mat, gis_triangle.geom)

#     triangle_2d = geometry.Polygon([
#         flat_triangle.a[:2],
#         flat_triangle.b[:2],
#         flat_triangle.c[:2],
#         flat_triangle.a[:2],
#     ])

#     intersection = []

#     for row in row_intersect:
#         # get the geometry
#         solid = row[1]
#         # apply same transformation than the flatten triangle
#         flatten_solid = transform_multipolygon(flat_mat, solid)

#         for s in flatten_solid:
#             try:
#                 it = triangle_2d.intersection(s)

#                 if it.geom_type == 'Polygon':
#                     intersection.append(it)
#                 elif it.geom_type == 'MultiPolygon':
#                     intersection.append(it)
#                 else:
#                     logger.error(
#                         'triangle_2d.intersection gave {} : ignored'.format(
#                             it.geom_type))

#             except TopologicalError as e:
#                 if not triangle_2d.is_valid:
#                     logger.error('triangle_2d is not valid')
#                     raise e

#                 if not s.is_valid:
#                     logger.error('S from flatten_solid is not valid')
#                     # on peut passer
#             except Exception as e:
#                 logger.debug(str(e))
#                 print(type(e))
#                 raise e

#     if len(intersection) == 0:
#         return gis_triangle.area
#     else:
#         try:
#             int_area = ops.cascaded_union(intersection).area
#             return gis_triangle.area - (
#                 int_area * gis_triangle.area / triangle_2d.area)
#         except Exception as e:
#             logger.error('Exception {}'.format(e))
#             logger.error('Error cascaded union for {}'.format(intersection))
#             logger.error('handle with gis_triangle.area')
#             return gis_triangle.area

# def t2p(t):
#     return geometry.Polygon([
#         t.a[:2],
#         t.b[:2],
#         t.c[:2],
#         t.a[:2],
#     ])


def append_it(intersection, pp):
    def inner(it):
        if it.geom_type == 'Polygon':
            intersection.append(it)
            pp(it)
        elif it.geom_type == 'MultiPolygon':
            # intersection.append(it)
            for g in it:
                inner(g)
        elif it.geom_type == 'GeometryCollection':
            for geom in it:
                inner(geom)
    #    else:
     #       logger.error('append_it {}'.format(it.geom_type))

    return inner


def noop(t, trans_mat, rot_mat, geom):
    pass


class Once:
    def __init__(self):
        self.used = False

    def take(self):
        if self.used:
            return False
        self.used = True
        return True


once = Once()


def get_exposed_area(gis_triangle, sunvec, row_intersect, post_process=None):
    try:
        center = gis_triangle.center
        trans_mat = translation_matrix(*(-center))
        rot_mat = get_flattening_mat(sunvec)
        flat_mat = rot_mat
    except GeometryMissingDimension:
        logger.error('Could not build a flattening matrix')
        return 1.0

    o = once.take()

    flat_triangle = transform_triangle(rot_mat, transform_triangle(trans_mat, gis_triangle.geom))

    triangle_2d = geometry.Polygon([
        flat_triangle.a[:2],
        flat_triangle.b[:2],
        flat_triangle.c[:2],
        flat_triangle.a[:2],
    ])

    # print('t2d.area: {}'.format(triangle_2d.area))

    intersection = []
    pp = partial(noop, 'append', trans_mat, rot_mat)
    # if o and post_process is not None:
     #   pp = partial(post_process, 'append', trans_mat, rot_mat)
    appender = append_it(intersection, pp)

    #pps = partial(noop, 'solid', trans_mat, rot_mat)
    #if o and post_process is not None:
     #   pps = partial(post_process, 'solid', trans_mat, rot_mat)

    for idx, solid in enumerate(row_intersect):
        #print('solid {} {}'.format(idx, len(solid)))
        # apply same transformation than the flatten triangle
        flatten_solid = transform_multipolygon(rot_mat, transform_multipolygon(trans_mat, solid))

        for s in flatten_solid:
        #    pps(s)
            try:
                appender(triangle_2d.intersection(s))
            except TopologicalError as e:
                if not triangle_2d.is_valid:
                    logger.error('triangle_2d is not valid')
                    raise e

                if not s.is_valid:
                    logger.error('S from flatten_solid is not valid')
                    # on peut passer
            except Exception as e:
                logger.error(str(e))
                raise e

    if len(intersection) == 0:
        print('No intersection')
        return 1.0
    else:
        try:
            intersection_area_2d = ops.cascaded_union(intersection).area
            exposed_area_2d = triangle_2d.area - intersection_area_2d
            exposed_rate = exposed_area_2d / triangle_2d.area

            return exposed_rate

        except Exception as e:
            logger.error('Exception {}'.format(e))
            logger.error('Error cascaded union for {}'.format(intersection))
            logger.error('handle with gis_triangle.area')
            return 1.0


# def worker(db, tmy, sample_rate, gis_triangles, with_shadows, day):
#     alb = 0.2
#     daily_radiations = []

#     for tim in day:
#         gh = tmy.get_float_average('G_Gh', tim, sample_rate)
#         dh = tmy.get_float_average('G_Dh', tim, sample_rate)
#         month = tim.month
#         tmy_index = tmy.get_index(tim)
#         hourly_radiations = []
#         for gis_triangle in gis_triangles:
#             with TimeCounter('triangle'):
#                 (center, sunpos, triangle_azimuth, triangle_inclination,
#                  triangle_area, triangle_rdiso,
#                  triangle_rdiso_flat) = init_triangle(tim, gis_triangle)

#                 if sunpos.is_daylight is False:
#                     continue

#                 # vector from center of triangle to sun position
#                 sunvec = sunpos.coords - center

#                 # radiation
#                 with TimeCounter('radiations'):
#                     radiation_global, radiation_direct = compute_gk(
#                         gh, dh, sunpos.sza, sunpos.saa, alb, triangle_azimuth,
#                         triangle_inclination, center[2], 1, month, tmy_index,
#                         triangle_rdiso_flat, triangle_rdiso)

#                     radiation_diffuse = radiation_global - radiation_direct

#                 if with_shadows:
#                     with TimeCounter('shadows'):
#                         direct_area = get_exposed_area(
#                             gis_triangle, sunvec,
#                             get_intersections_for_triangle(
#                                 gis_triangle, sunvec, db))
#                 else:
#                     direct_area = triangle_area

#                 total_diffuse = triangle_area * radiation_diffuse
#                 total_direct = direct_area * radiation_direct

#                 gis_triangle.radiations.append(total_direct + total_diffuse)
#                 hourly_radiations.append(total_direct + total_diffuse)

#         daily_radiations.append(np.sum(hourly_radiations))

#     return np.sum(daily_radiations)

# def get_results_roof(db, tmy, sample_rate, roof_id, with_shadows=False):

#     days = generate_sample_days(sample_rate)
#     roof = list(rows_with_geom(db, 'select_roof', (roof_id, ), 1))[0]
#     gis_triangles = []
#     print('roof({})'.format(roof_id))
#     for t in tesselate(roof[1]):
#         gis_t = GISTriangle(t)
#         gis_t.init(db)
#         gis_triangles.append(gis_t)

#     radiations = []

#     with TimeCounter('total'):
#         with ThreadPoolExecutor() as executor:
#             for daily_radiation in executor.map(
#                     partial(worker, db, tmy, sample_rate, gis_triangles,
#                             with_shadows), days):
#                 radiations.append(daily_radiation * float(sample_rate))

#     features = []
#     for t in gis_triangles:
#         t.radiations = t.radiations * sample_rate
#         features.append(triangle_to_geojson(t))

#     return shape_to_feature(roof[1], roof_id,
#                             dict(irradiance=np.sum(radiations), area=roof[2]))


def get_roof_tilt(geom):
    angles = []
    areas = []
    for t in tesselate(geom):
        area = get_triangle_area(t)
        angles.append(get_triangle_inclination(t) * area)
        areas.append(area)

    return sum(angles) / sum(areas)


def get_roof_azimuth(geom):
    azimuths = []
    areas = []
    for t in tesselate(geom):
        area = get_triangle_area(t)
        azimuths.append(get_triangle_azimut(t) * area)
        areas.append(area)

    return sum(azimuths) / sum(areas)


def get_roof_area(geom):
    return sum([get_triangle_area(t) for t in tesselate(geom)])
