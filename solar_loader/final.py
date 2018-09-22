import itertools as it
from functools import partial
from psycopg2.extensions import AsIs
import django
from django.conf import settings
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from .store import Data
from .tmy import TMY
from .records import GisTriangle, Triangle
from .time import generate_sample_days
from .geom import (
    get_flattening_mat,
    get_triangle_area,
    get_triangle_azimut,
    get_triangle_center,
    get_triangle_inclination,
    tesselate,
    unit_vector,
)
from .sunpos import get_sun_position, get_coords_from_angles
from .lingua import make_polyhedral, rows_with_geom
from .compute import get_exposed_area, get_roof_area
from .rdiso import get_rdiso5
from .radiation import compute_gk
from .rad5 import rad5

django.setup()
# db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
results_db = Data(settings.SOLAR_CONNECTION_RESULTS, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)

sample_rate = getattr(settings, 'SOLAR_SAMPLE_RATE', 14)
with_shadows = getattr(settings, 'SOLAR_WITH_SHADOWS', True)


def round5(f):
    mul = f // 5
    if f % 5 > 2.5:
        mul += 1
    return mul * 5


def compute_radiation(exposed_area, tim, triangle):
    # return rad5(round5(triangle.tilt), round5(
    #     triangle.azimuth)) * triangle.area
    rdiso_flat, rdiso = get_rdiso5(
        round5(triangle.azimuth), round5(triangle.tilt))
    gh = tmy.get_float_average('G_Gh', tim, sample_rate)
    dh = tmy.get_float_average('G_Dh', tim, sample_rate)
    hs = tmy.get_float('hs', tim)
    Az = tmy.get_float('Az', tim)
    month = tim.month
    tmy_index = tmy.get_index(tim)

    radiation_global, radiation_direct = compute_gk(
        gh,
        dh,
        90.0 - hs,
        Az,
        0.2,
        triangle.azimuth,
        triangle.tilt,
        28,  # Meteonorm 7 Output Preview for Bruxelles centre
        1,
        month,
        tmy_index,
        rdiso_flat,
        rdiso)

    diffuse = triangle.area * (radiation_global - radiation_direct)
    direct = exposed_area * radiation_direct

    return (diffuse + direct) * sample_rate  # / triangle.area  # * sample_rate


def query_intersections(db, triangle, sunvec):
    nearvec = sunvec * 1.0
    farvec = sunvec * 200.0
    triangle_near = Triangle(triangle.a + nearvec, triangle.b + nearvec,
                             triangle.c + nearvec)
    triangle_far = Triangle(triangle.a + farvec, triangle.b + farvec,
                            triangle.c + farvec)
    polyhedr = make_polyhedral(triangle_near, triangle_far)

    return list(rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ), 1))


def make_task(day, tr):
    # sunpos_s = [get_sun_position(tr.center, ti) for ti in day]
    # sunvec_s = [
    #     unit_vector(
    #         get_coords_from_angles(tr.center, sunpos.elevation, sunpos.azimuth)
    #         - tr.center) for sunpos in sunpos_s
    # ]

    time_and_vec = []
    for ti in day:
        sunpos = get_sun_position(tr.center, ti)
        sunvec = unit_vector(
            get_coords_from_angles(tr.center, sunpos.elevation, sunpos.azimuth)
            - tr.center)
        time_and_vec.append((ti, sunvec))

    def chain(db, executor):
        rad = 0
        get_intersections = lambda tv: query_intersections(db, tr.geom, tv[1])
        for (ti, sunvec), row_intersect in zip(
                time_and_vec, executor.map(get_intersections, time_and_vec)):
            exposed_area = get_exposed_area(tr, sunvec, row_intersect)
            rad += compute_radiation(exposed_area, ti, tr)
        return rad

    return chain


def process_tasks(roof_geometry, db, executor):
    triangles = []
    days = generate_sample_days(sample_rate)
    for geom in tesselate(roof_geometry):
        triangles.append(
            GisTriangle(
                geom,
                get_triangle_azimut(geom),
                get_triangle_inclination(geom),
                get_triangle_center(geom),
                get_triangle_area(geom),
            ))

    tasks = [make_task(day, tr) for day, tr in it.product(days, triangles)]

    return map(lambda t: t(db, executor), tasks)


def compute_radiation_for_roof(row):
    print('compute_radiation_for_roof({})'.format(row[0]))
    id = row[0]
    geom = row[1]
    area = get_roof_area(geom)
    db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)

    with ThreadPoolExecutor() as executor:
        total_rad = sum(process_tasks(geom, db, executor))

    return id, total_rad / area


def insert_result(r):
    print('insert_result({})'.format(r))
    results_db.exec('insert_result', r)
    return r[0]


def compute_for_all(limit):
    results_db.exec('drop_result')
    results_db.exec('create_result')
    db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    # dones = []
    with ProcessPoolExecutor() as executor:
        if limit is not None:
            rows = rows_with_geom(db, 'select_roof_all_limit', (limit, ), 1)
        else:
            rows = rows_with_geom(db, 'select_roof_all', (), 1)

        # proc = lambda row: (row[0], compute_radiation_for_roof(row[1]))

        for roof_id, rad in executor.map(
                compute_radiation_for_roof, rows, chunksize=4):
            # print('{} => {}'.format(roof_id, rad))
            # dones.append((roof_id, rad))
            insert_result((
                roof_id,
                rad,
            ))

    # with ThreadPoolExecutor() as executor:
    #     for i in executor.map(insert_result, dones):
    #         print('inserted {}'.format(i))