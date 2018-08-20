import os
from collections import namedtuple
from functools import partial
from datetime import datetime, timedelta, timezone
import numpy as np
import math
from collections import deque
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
from psycopg2.extensions import AsIs
from shapely import geometry, wkb, wkt, affinity
from django.conf import settings
import logging
from .records import Triangle
from .gis_geom import GISTriangle
from .lingua import make_polyhedral_p, rows_with_geom, triangle_to_geojson, make_polyhedral
from .sunpos import get_sun_position, SunposNight
from .geom import (tesselate, get_triangle_mat, transform_triangle,
                   unit_vector, transform_multipolygon,
                   GeometryMissingDimension, vec3_add, multipoly_bbox)
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


def generate_sample_times(sample_interval):
    for day in generate_sample_days(sample_interval):
        for tim in day:
            yield tim


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

# def rows_with_geom_t(db, select, params, geom_index):
#     if use_wkb:
#         with TimeCounter('rows_with_geom_t'):
#             for row in db.rows(select, {'conv_geom_operator': 'ST_AsBinary'},
#                                params):
#                 row = list(row)
#                 with TimeCounter('wkb.loads'):
#                     row[geom_index] = wkb.loads(row[geom_index], hex=False)
#                 yield row
#     else:
#         with TimeCounter('rows_with_geom_t#{}'.format(select)):
#             for row in db.rows(select, {'conv_geom_operator': 'st_astext'},
#                                params):
#                 row = list(row)
#                 with TimeCounter('wkt.loads'):
#                     try:
#                         row[geom_index] = wkt.loads(row[geom_index])
#                     except Exception as ex:
#                         logger.error('could not read "{}"\n{}'.format(
#                             row[geom_index], ex))
#                         continue
#                 yield row


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


def translate_poly(p, v, u):
    vec = v * u
    return affinity.translate(p, vec[0], vec[1], vec[2])


def get_intersections_for_parcel(db, roofs, day):
    """Maps times of day into collections of intersecting solids
    """
    poly_roofs = list(map(lambda r: r[0], roofs))
    minx, miny, minz, maxx, maxy, maxz = multipoly_bbox(poly_roofs)
    logger.info('{} {} {} {} {} {}'.format(minx, miny, minz, maxx, maxy, maxz))
    center = np.array([
        minx + ((maxx - minx) / 2.0),
        miny + ((maxy - miny) / 2.0),
        minz + ((maxz - minz) / 2.0),
    ])

    base = geometry.Polygon([
        [minx, miny, minz],
        [minx, maxy, minz],
        [maxx, maxy, minz],
        [maxx, miny, minz],
        [minx, miny, minz],
    ])
    # logger.info('roofs:\n{}'.format(list(map(lambda r: r.to_wkt(), roofs))))
    # logger.info('center:\n{}'.format(center))
    # logger.info('base:\n{}'.format(base.to_wkt()))

    results = []
    for tim in day:
        sunpos = get_sun_position(center, tim)
        if sunpos.is_daylight is False:
            results.append((tim, []))
            continue

        sunvec = sunpos.coords - center
        sunvecunit = unit_vector(sunvec)
        nearvec = sunvecunit * 0.1
        farvec = sunvecunit * 200.0
        poly_near = affinity.translate(base, nearvec[0], nearvec[1],
                                       nearvec[2])
        poly_far = affinity.translate(base, farvec[0], farvec[1], farvec[2])
        polyhedr = make_polyhedral_p(poly_near, poly_far)

        with TimeCounter('intersect'):
            results.append((
                tim,
                list(
                    rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ),
                                   1)),
            ))
    return results


class IntersectionsNotFound(Exception):
    pass


def find_intersections_t(intersections, tim):
    for t, i in intersections:
        if t == tim:
            return i
    raise IntersectionsNotFound(tim)


def get_intersections(roof, gis_triangles, tim, db):
    if len(gis_triangles) == 0:
        raise EmptyRoof()

    gis_triangle = gis_triangles[0]

    return get_intersections_for_triangle(gis_triangle, tim, db)


def get_intersections_for_triangle(gis_triangle, tim, db):

    center, sunpos, _, _, _, _, _ = init_triangle(tim, gis_triangle)
    sunvec = sunpos.coords - center
    sunvecunit = unit_vector(sunvec)

    # vector of length 0.1m towards sun position
    nearvec = sunvecunit * 0.1
    # vector of length 200m towards sun position
    farvec = sunvecunit * 200

    # layered polygons
    # polys = geometry.MultiPolygon(
    #     map(partial(translate_poly, roof[0], sunvecunit), range(1, 2

    #     00, 2)))
    # polyhedr = 'ST_GeomFromText(\'{}\', 31370)'.format(wkt.dumps(polys))

    # back to real polyhedral
    t0 = Triangle(*vec3_add(gis_triangle.geom, nearvec))
    t1 = Triangle(*vec3_add(gis_triangle.geom, farvec))
    polyhedr = make_polyhedral(t0, t1)

    # a polyhedral surface from roof towards sun
    # poly_near = affinity.translate(gis_triangle.to_polygon(), nearvec[0],
    #                                nearvec[1], nearvec[2])
    # poly_far = affinity.translate(gis_triangle.to_polygon(), farvec[0],
    #                               farvec[1], farvec[2])
    # polyhedr = make_polyhedral_p(poly_near, poly_far)

    return rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ), 1)


def get_exposed_area(gis_triangle, triangle_area, sunvec, row_intersect):
    try:
        flat_mat = get_triangle_mat(sunvec)
    except GeometryMissingDimension:
        return triangle_area

    flat_triangle = transform_triangle(flat_mat, gis_triangle.geom)

    triangle_2d = geometry.Polygon([
        flat_triangle.a[:2],
        flat_triangle.b[:2],
        flat_triangle.c[:2],
        flat_triangle.a[:2],
    ])

    intersection = None

    # end_time_record('intersect')

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
                        logger.debug(str(triangle_2d.is_valid))
                        logger.debug(str(s.is_valid))
                        logger.debug(str(exc))

    if intersection is None:
        return triangle_area
    else:
        return intersection.area * triangle_area / triangle_2d.area


def worker3(db, tmy, gis_triangle_tim):
    gis_triangle, tim = gis_triangle_tim
    gh = tmy.get_float('Global Horizontal Radiation', tim)
    dh = tmy.get_float('Diffuse Horizontal Radiation', tim)
    alb = 0.2
    month = tim.month
    tmy_index = tmy.get_index(tim)
    with TimeCounter('triangle'):
        center, sunpos, triangle_azimuth, triangle_inclination, triangle_area, triangle_rdiso, triangle_rdiso_flat = init_triangle(
            tim, gis_triangle)

        if sunpos.is_daylight is False:
            return 0

        # vector from center of triangle to sun position
        sunvec = sunpos.coords - center

        # radiation
        with TimeCounter('radiations'):
            radiation_global, radiation_direct = compute_gk(
                gh, dh, sunpos.sza, sunpos.saa, alb, triangle_azimuth,
                triangle_inclination, center[2], 1, month, tmy_index,
                triangle_rdiso_flat, triangle_rdiso)

        direct_area = get_exposed_area(
            gis_triangle, triangle_area, sunvec,
            get_intersections_for_triangle(gis_triangle, tim, db))
        total_global = triangle_area * radiation_global
        total_direct = direct_area * radiation_direct

        gis_triangle.radiations.append(total_direct + total_global)
        return total_direct + total_global


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
            sunpos = get_sun_position(gis_triangles[0].geom.a, tim)
            if sunpos.is_daylight is False:
                continue
            try:
                with TimeCounter('intersect.query'):
                    row_intersect = list(
                        get_intersections(roof, gis_triangles, tim, db))
            except EmptyRoof:
                continue

            for gis_triangle in gis_triangles:
                center, sunpos, triangle_azimuth, triangle_inclination, triangle_area, triangle_rdiso, triangle_rdiso_flat = init_triangle(
                    tim, gis_triangle)

                if sunpos.is_daylight is False:
                    continue

                # with TimeCounter('intersect.query'):
                #     row_intersect = list(
                #         get_intersections_for_triangle(gis_triangle, tim, db))
                #     print('Intersects {}, {}'.format(tim, len(row_intersect)))

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

                for row in row_intersect:
                    with TimeCounter('intersect.compute'):
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
                    print('R: {} {:.2f}'.format(len(row_intersect), 100))
                else:
                    direct_area = intersection.area * triangle_area / triangle_2d.area
                    print('R: {} {:.2f}'.format(
                        len(row_intersect), direct_area * 100.0 / triangle_area))
                    total_direct = direct_area * radiation_direct

                hourly_radiations.append(total_direct + total_global)
                gis_triangle.radiations.append(total_direct + total_global)
                # end of shadow

        daily_radiations.append(np.sum(hourly_radiations))

    logger.debug('End {}-{}-{} ({})\n{}'.format(
        day[0].year, day[0].month, day[0].day,
        perf_counter() - start_time, daily_radiations))
    return np.sum(daily_radiations)


def worker2(db, tmy, t_roofs, intersections, tim):
    daily_radiations = []

    with TimeCounter('worker2'):
        # values for compute_ck
        gh = tmy.get_float('Global Horizontal Radiation', tim)
        dh = tmy.get_float('Diffuse Horizontal Radiation', tim)
        alb = 0.2
        month = tim.month
        tmy_index = tmy.get_index(tim)

        hourly_radiations = []

        for roof, gis_triangles in t_roofs:

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
                    for row in find_intersections_t(intersections, tim):
                        # get the geometry
                        solid = row[1]
                        # apply same transformation than the flatten triangle
                        with TimeCounter('flatten_trans_poly'):
                            flatten_solid = transform_multipolygon(
                                flat_mat, solid)
                        # drops its z
                        # solid_2d, zs = multipolygon_drop_z(flatten_solid)
                        with TimeCounter('flatten_solid_loop'):
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


def get_triangles(db, ground_id, roofs):

    gis_triangles = []
    for i, roof in enumerate(roofs):
        triangles = tesselate(roof)
        for t in triangles:
            gis_t = GISTriangle(t, i, ground_id)
            gis_t.init(db)
            gis_triangles.append(gis_t)

    return gis_triangles


def get_results(db, tmy, sample_interval, ground_id):
    times_queue.clear()

    with TimeCounter('compute_triangles'):
        # We start at equinox
        days = generate_sample_days(sample_interval)

        # we get roofs for this ground
        roofs = [
            row[0] for row in rows_with_geom(db, 'select_roof_within', (
                ground_id, ), 0)
        ]

        t_roofs = make_t_roofs(db, ground_id, roofs)

    radiations = []
    # times = list(generate_sample_times(sample_interval))
    # gis_triangles = []
    # units = []
    # for gt in get_triangles(db, ground_id, roofs):
    #     for tim in times:
    #         units.append((
    #             gt,
    #             tim,
    #         ))

    with TimeCounter('total'):
        with ThreadPoolExecutor() as executor:
            for daily_radiation in executor.map(
                    partial(worker, db, tmy, t_roofs), days):
                radiations.append(daily_radiation * float(sample_interval))

    # total_area = np.sum([t.area for t in gis_triangles])
    # logger.info('radiations on {} amounts to {} KWh on {} m2'.format(
    #     ground_id, int(math.floor(np.sum(radiations) / 1000)), total_area))
    # logger.info('Done {}'.format(perf_counter() - start))

    summarize_times()

    features = []
    for _, gis_triangles in t_roofs:
        for t in gis_triangles:
            t.radiations = t.radiations * sample_interval
            features.append(triangle_to_geojson(t))

    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::31370"
            }
        },
        "features": features,
        "radiations": radiations,
    }


def make_t_roofs(db, ground_id, roofs):
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
    return t_roofs


def get_results_2(db, tmy, sample_interval, ground_id):
    times_queue.clear()

    with TimeCounter('total'):
        # We start at equinox
        days = generate_sample_days(sample_interval)

        # we get roofs for this ground
        roofs = [
            row[0] for row in rows_with_geom(db, 'select_roof_within', (
                ground_id, ), 0)
        ]

        t_roofs = make_t_roofs(db, ground_id, roofs)
        radiations = []

        its = []

        # with TimeCounter('exe_thread'):
        with ThreadPoolExecutor() as executor:
            # its = zip(
            #     days,
            #     executor.map(
            #         partial(get_intersections_for_parcel, db, roofs),
            #         days))

            for day, intersections in zip(
                    days,
                    executor.map(
                        partial(get_intersections_for_parcel, db, roofs),
                        days)):
                with ProcessPoolExecutor() as pexec:
                    f = partial(worker2, db, tmy, t_roofs, intersections)
                    for daily_radiation in pexec.map(f, day):
                        radiations.append(
                            daily_radiation * float(sample_interval))
                    pexec.submit(summarize_times)
                #     daily_radiation = worker2(db, tmy, t_roofs, day, intersections)
                #     radiations.append(daily_radiation * float(sample_interval))
                # for daily_radiation in worker2(db, tmy, t_roofs, day, intersections):
                #     radiations.append(daily_radiation * float(sample_interval))

        # with TimeCounter('exe_process'):
        #     with ProcessPoolExecutor() as executor:
        #         for day, intersections in its:
        #             daily_radiation = worker2(db, tmy, t_roofs, day,
        #                                       intersections)
        #             radiations.append(daily_radiation * float(sample_interval))

    summarize_times()