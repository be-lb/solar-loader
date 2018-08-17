import os
from collections import namedtuple
from datetime import datetime, timedelta, timezone
import numpy as np
import math
from collections import deque
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from psycopg2.extensions import AsIs
from shapely import geometry, wkb, wkt, affinity
from django.conf import settings
import logging
from .records import Triangle
from .gis_geom import GISTriangle
from .lingua import make_polyhedral_p, rows_with_geom, triangle_to_geojson
from .sunpos import get_sun_position, SunposNight
from .geom import (tesselate, get_triangle_mat, transform_triangle,
                   unit_vector, transform_multipolygon,
                   GeometryMissingDimension, vec3_add)
from .radiation import compute_gk

logger = logging.getLogger(__name__)


def fake_compute_gk(*args):
    """A noop implementation to measure time of computaion without actually computing radiation
    """
    return (
        1.0,
        1.0,
    )


if 'FAKE_COMPUTE' in os.environ.keys():
    compute_gk = fake_compute_gk


def time_range(start, interval, n):
    return [start + (interval * i) for i in range(n)]


def get_days(start_month, start_day, interval, n):
    start = datetime(
        datetime.now(timezone.utc).year, start_month, start_day, 0, 0, 0, 0,
        timezone.utc)
    d = timedelta(hours=1)
    days = []
    for t in time_range(start, interval, n):
        days.append([t + (d * i) for i in range(24)])
    return days


def generate_sample_days(sample_interval):
    sample_rate = 365 / sample_interval
    days = get_days(3, 20, timedelta(days=sample_interval), int(sample_rate))
    return days


def same_triangle(t0, t1):
    # TODO pas utilisé
    e = 0.001
    for v in (0, 1, 2):
        for c in (0, 1, 2):
            d = abs(t0[v][c] - t1[v][c])
            if d > e:
                return False
    return True


# Time recording
# start = {}
# compute_time = {}

times_queue = deque()
Timed = namedtuple('Timed', ['counter', 't'])


class TimeCounter:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = perf_counter()

    def __exit__(self, *args):
        times_queue.append(Timed(self.name, perf_counter() - self.start))


# def start_time_record(counter_name):
#     global start
#     start[counter_name] = perf_counter()

# def end_time_record(counter_name):
#     global compute_time
#     if counter_name not in compute_time:
#         compute_time[counter_name] = []
#     compute_time[counter_name].append(perf_counter() - start[counter_name])

# compute_gk_times = []
use_wkb = True
if hasattr(settings, 'SOLAR_WKT_FROM_DB') and settings.SOLAR_WKT_FROM_DB:
    use_wkb = False


def rows_with_geom_t(db, select, params, geom_index):
    if use_wkb:
        with TimeCounter('rows_with_geom_t'):
            for row in db.rows(select, {'conv_geom_operator': 'ST_AsBinary'},
                               params):
                row = list(row)
                with TimeCounter('wkb.loads'):
                    row[geom_index] = wkb.loads(row[geom_index], hex=False)
                yield row
    else:
        with TimeCounter('rows_with_geom_t#{}'.format(select)):
            for row in db.rows(select, {'conv_geom_operator': 'st_astext'},
                               params):
                row = list(row)
                with TimeCounter('wkt.loads'):
                    row[geom_index] = wkt.loads(row[geom_index])
                yield row


def init_triangle(tim, gis_triangle):
    center = gis_triangle.center
    sunpos = get_sun_position(center, tim)

    # if sunpos.is_daylight is False:
    #     raise SunposNight()

    triangle_azimuth = gis_triangle.get_azimuth()
    triangle_inclination = gis_triangle.get_inclination()

    triangle_area = gis_triangle.area
    triangle_rdiso = gis_triangle.get_rdiso()
    triangle_rdiso_flat = gis_triangle.get_rdiso_flat()

    return (center, sunpos, triangle_azimuth, triangle_inclination,
            triangle_area, triangle_rdiso, triangle_rdiso_flat)


class EmptyRoof(Exception):
    pass


def get_intersections(roof, gis_triangles, tim, db):
    if len(gis_triangles) == 0:
        raise EmptyRoof()

    gis_triangle = gis_triangles[0]

    center, sunpos, _, _, _, _, _ = init_triangle(tim, gis_triangle)
    sunvec = sunpos.coords - center
    sunvecunit = unit_vector(sunvec)

    # vector of length 0.1m towards sun position
    nearvec = sunvecunit * 0.1
    # vector of length 200m towards sun position
    farvec = sunvecunit * 200

    poly_near = affinity.translate(roof[0], nearvec[0], nearvec[1], nearvec[2])
    poly_far = affinity.translate(roof[0], farvec[0], farvec[1], farvec[2])

    # a polyhedral surface from roof towards sun
    polyhedr = make_polyhedral_p(poly_near, poly_far)

    return rows_with_geom_t(db, 'select_intersect', (AsIs(polyhedr), ), 1)


def worker(db, tmy, t_roofs, day):
    start_time = perf_counter()
    logger.debug('Start {}-{}-{}'.format(day[0].year, day[0].month,
                                         day[0].day))
    daily_radiations = []

    for tim in day:
        # values for compute_ck
        gh = tmy.get_float('Global Horizontal Radiation', tim)
        dh = tmy.get_float('Diffuse Horizontal Radiation', tim)
        alb = 0.2
        month = tim.month
        tmy_index = tmy.get_index(tim)

        hourly_radiations = []

        for roof, gis_triangles in t_roofs:
            try:
                row_intersect = get_intersections(roof, gis_triangles, tim, db)
            except EmptyRoof:
                continue

            for gis_triangle in gis_triangles:
                with TimeCounter('init_triangle'):
                    center, sunpos, triangle_azimuth, triangle_inclination, triangle_area, triangle_rdiso, triangle_rdiso_flat = init_triangle(
                        tim, gis_triangle)

                    if sunpos.is_daylight is False:
                        continue

                # # vector from center of triangle to sun position
                sunvec = sunpos.coords - center
                # sunvecunit = unit_vector(sunvec)

                # radiation
                with TimeCounter('radiations'):
                    radiation_global, radiation_direct = compute_gk(
                        gh, dh, sunpos.sza, sunpos.saa, alb, triangle_azimuth,
                        triangle_inclination, center[2], 1, month, tmy_index,
                        triangle_rdiso_flat, triangle_rdiso)

                try:
                    flat_mat = get_triangle_mat(sunvec)
                except GeometryMissingDimension:
                    continue

                flat_triangle = transform_triangle(flat_mat, gis_triangle.geom)

                triangle_2d = geometry.Polygon([
                    flat_triangle.a[:2],
                    flat_triangle.b[:2],
                    flat_triangle.c[:2],
                    flat_triangle.a[:2],
                ])

                intersection = None

                # end_time_record('intersect')

                with TimeCounter('shadow'):
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
                                if intersection is None:
                                    intersection = it
                                elif it.geom_type == 'Polygon':
                                    intersection = intersection.union(it)
                            except Exception as exc:
                                logger.debug(str(triangle_2d.is_valid))
                                logger.debug(str(s.is_valid))
                                print(str(exc))

                    total_global = triangle_area * radiation_global
                    if intersection is None:
                        total_direct = triangle_area * radiation_direct
                    else:
                        direct_area = intersection.area * triangle_area / triangle_2d.area
                        total_direct = direct_area * radiation_direct

                    hourly_radiations.append(total_direct + total_global)
                    gis_triangle.radiations.append(total_direct + total_global)
                    # end of shadow

        daily_radiations.append(np.sum(hourly_radiations))

    logger.debug('End {}-{}-{} ({})\n{}'.format(
        day[0].year, day[0].month, day[0].day,
        perf_counter() - start_time, daily_radiations))
    return np.sum(daily_radiations)


def summarize_times():
    keys = []
    for ct in times_queue:
        if ct.counter not in keys:
            keys.append(ct.counter)

    for k in sorted(keys):
        values = list(
            map(lambda x: x.t, filter(lambda x: x.counter == k, times_queue)))
        logger.info('Time spent in {}: n = {}, t = {} (s)'.format(
            k, len(values), np.sum(values)))


def get_results(db, tmy, sample_interval, ground_id):
    times_queue.clear()
    start = perf_counter()

    with TimeCounter('compute_triangles'):
        # We start at equinox
        days = generate_sample_days(sample_interval)

        # we get roofs for this ground
        roofs = [
            row[0] for row in rows_with_geom(db, 'select_roof_within', (
                ground_id, ), 0)
        ]

        # triangles_row = []
        t_roofs = []

        for i, roof in enumerate(roofs):
            gis_triangles = []
            triangles = tesselate(roof)
            for t in triangles:
                gis_t = GISTriangle(t, i, ground_id)
                gis_t.init(db)
                gis_triangles.append(gis_t)
            t_roofs.append((
                roof,
                gis_triangles,
            ))
            # triangles_row.extend(triangles)

        # end_time_record('compute_triangles')

    logger.info(
        'Start processing {} triangles over {} roof surfaces for {} days'.
        format(len(gis_triangles), len(roofs), len(days)))
    radiations = []

    with ThreadPoolExecutor() as executor:
        for daily_radiation in executor.map(
                partial(worker, db, tmy, t_roofs), days):
            radiations.append(daily_radiation * float(sample_interval))

    total_area = np.sum([t.area for t in gis_triangles])
    logger.info('radiations on {} amounts to {} KWh on {} m2'.format(
        ground_id, int(math.floor(np.sum(radiations) / 1000)), total_area))
    logger.info('Done {}'.format(perf_counter() - start))

    # for cn in sorted(compute_time.keys):
    #     logger.info('Time spent in {}: n = {}, t = {} (s)'.format(
    #         cn, len(compute_time[cn]), np.sum(compute_time[cn])))

    summarize_times()

    logger.info(
        '{} seconds spent in db with an average of {} seconds for {} executions'.
        format(db.total_time(), db.mean_time(), db.total_exec()))

    for t in gis_triangles:
        t.radiations = t.radiations * sample_interval

    logger.debug('Check')
    logger.debug("{}".format(np.sum(radiations)))
    logger.debug("{}".format(
        np.sum([np.sum(t.radiations) for t in gis_triangles])))

    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::31370"
            }
        },
        "features": [triangle_to_geojson(t) for t in gis_triangles],
        "radiations": radiations,
    }
