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
from shapely import affinity, geometry, wkb, wkt

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

brussels_zone = timezone('Europe/Brussels')


def time_range(start, interval, n, tz=None):
    if tz is None:
        return [start + (interval * i) for i in range(n)]
    return [start.astimezone(tz) + (interval * i) for i in range(n)]


def get_days(start_month, start_day, interval, n):
    start = datetime(
        datetime.now(brussels_zone).year, start_month, start_day, 0, 0, 0, 0,
        brussels_zone)
    d = timedelta(hours=1)
    days = []
    for t in time_range(start, interval, n):
        days.append([t + (d * i) for i in range(24)])
    return days


def generate_sample_days(sample_rate):
    sample_rate = 365 / sample_rate
    days = get_days(3, 21, timedelta(days=sample_rate), int(sample_rate))
    return days


def generate_sample_times(sample_rate):
    for day in generate_sample_days(sample_rate):
        for tim in day:
            yield tim


times_queue = deque()
Timed = namedtuple('Timed', ['counter', 't'])


class TimeCounter:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = perf_counter()

    def __exit__(self, *args):
        times_queue.append(Timed(self.name, perf_counter() - self.start))


def get_intersections_for_triangle(tim, db, sunvec, gis_triangle):
    # print('get_intersections_for_triangle({}, {}, {}, {})'.format(
    #     tim, db, sunvec, gis_triangle))
    sunvecunit = unit_vector(sunvec)

    # vector of length 0.1m towards sun position
    nearvec = sunvecunit * 1.0  #0.1
    # vector of length 200m towards sun position
    farvec = sunvecunit * 200.0

    # layered polygons
    # polys = geometry.MultiPolygon(
    #     map(partial(translate_poly, roof[0], sunvecunit), range(1, 2

    #     00, 2)))
    # polyhedr = 'ST_GeomFromText(\'{}\', 31370)'.format(wkt.dumps(polys))

    # back to real polyhedral
    triangle_near = Triangle(gis_triangle.geom.a + nearvec,
                             gis_triangle.geom.b + nearvec,
                             gis_triangle.geom.c + nearvec)
    triangle_far = Triangle(gis_triangle.geom.a + farvec,
                            gis_triangle.geom.b + farvec,
                            gis_triangle.geom.c + farvec)
    polyhedr = make_polyhedral(triangle_near, triangle_far)
    # db.exec('insert_polyhedral', (tim, AsIs(polyhedr)))

    # a polyhedral surface from roof towards sun
    # poly_near = affinity.translate(gis_triangle.to_polygon(), nearvec[0],
    #                                nearvec[1], nearvec[2])
    # poly_far = affinity.translate(gis_triangle.to_polygon(), farvec[0],
    #                               farvec[1], farvec[2])
    # polyhedr = make_polyhedral_p(poly_near, poly_far)

    return list(rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ), 1))


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

    intersection = None

    with TimeCounter('intersections'):
        for row in row_intersect:
            # get the geometry
            solid = row[1]
            # apply same transformation than the flatten triangle
            with TimeCounter('intersections.local'):
                flatten_solid = transform_multipolygon(flat_mat, solid)
                # drops its z
                # solid_2d, zs = multipolygon_drop_z(flatten_solid)
                for s in flatten_solid:
                    try:
                        it = triangle_2d.intersection(s)
                        if intersection is None:
                            intersection = it
                        elif it.geom_type == 'Polygon':
                            intersection = intersection.union(it)
                    except Exception as exc:
                        logger.debug(str(exc))

    if intersection is None:
        return gis_triangle.area
    else:
        # print('R: {} {:.2f} {:.2f}'.format(
        #     len(row_intersect), intersection.area, triangle_2d.area))
        return gis_triangle.area - (
            intersection.area * gis_triangle.area / triangle_2d.area)


def compute_for_triangles(db, tmy, sample_rate, gis_triangles, with_shadows,
                          day):

    print('compute_for_triangles')
    alb = 0.2
    daily_radiations = []

    for tim in day:
        gh = tmy.get_float_average('G_Gh', tim, sample_rate)
        dh = tmy.get_float_average('G_Dh', tim, sample_rate)
        hs = tmy.get_float('hs', tim)
        Az = tmy.get_float('Az', tim)
        month = tim.month
        tmy_index = tmy.get_index(tim)
        hourly_radiations = []

        if hs < 1:
            continue

        triangles = list(map(
            lambda t: (get_coords_from_angles(t.center, hs, Az) - t.center, t,), gis_triangles))

        def fn(st):
            sunvec, triangle = st
            return get_intersections_for_triangle(tim, db, sunvec, triangle)

        with ThreadPoolExecutor() as executor:
            # print('compute_for_triangles')
            for (sunvec, triangle), row_intersect in zip(
                    triangles, executor.map(fn, triangles)):
                # for triangle in gis_triangles:
                #     sunpos = get_coords_from_angles(triangle.center, hs, Az)
                #     sunvec = sunpos - triangle.center
                # if hs < 1:
                #     continue

                radiation_global, radiation_direct = compute_gk(
                    gh, dh, 90 - hs, Az, alb, triangle.get_azimuth(),
                    triangle.get_inclination(), triangle.center[2], 1, month,
                    tmy_index, triangle.get_rdiso_flat(), triangle.get_rdiso())

                radiation_diffuse = radiation_global - radiation_direct

                if with_shadows:
                    direct_area = get_exposed_area(
                        triangle,
                        triangle.area,
                        sunvec,
                        row_intersect,
                    )
                else:
                    direct_area = triangle.area

                total_diffuse = triangle.area * radiation_diffuse
                total_direct = direct_area * radiation_direct

                hourly_radiations.append(total_direct + total_diffuse)

        daily_radiations.append(np.sum(hourly_radiations))

    return np.sum(daily_radiations)


def summarize_times():
    keys = []
    for ct in times_queue:
        if ct.counter not in keys:
            keys.append(ct.counter)

    for k in sorted(keys):
        values = list(
            map(lambda x: x.t, filter(lambda x: x.counter == k, times_queue)))
        n = len(values)
        t = np.sum(values)
        print('Time spent in {}: n = {}, t = {:.2f} s, t/n = {:.2f} ms'.format(
            k, n, t, (t / float(n)) * 1000.0))


def get_triangles(db, roof_geom):
    for t in tesselate(roof_geom):
        gis_t = GISTriangle(t)
        gis_t.init(db)
        yield gis_t


def get_results_roof(db, tmy, sample_rate, roof_id, with_shadows=False):
    times_queue.clear()
    days = generate_sample_days(sample_rate)
    roof = list(rows_with_geom(db, 'select_roof', (roof_id, ), 1))[0]
    gis_triangles = list(get_triangles(db, roof[1]))

    radiations = []

    with TimeCounter('total'):
        with ThreadPoolExecutor() as executor:
            for daily_radiation in executor.map(
                    partial(compute_for_triangles, db, tmy, sample_rate,
                            gis_triangles, with_shadows), days):
                radiations.append(daily_radiation * float(sample_rate))

    features = []
    for t in gis_triangles:
        t.radiations = t.radiations * sample_rate
        features.append(triangle_to_geojson(t))

    return shape_to_feature(
        roof[1], roof_id, dict(productivity=np.sum(radiations), area=roof[2]))
