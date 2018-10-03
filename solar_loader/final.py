import itertools as it
from functools import partial
import logging
from psycopg2.extensions import AsIs
import django
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from .time import now
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

logger = logging.getLogger(__name__)

django.setup()
tmy = TMY(settings.SOLAR_TMY)

sample_rate = getattr(settings, 'SOLAR_SAMPLE_RATE', 14)
with_shadows = getattr(settings, 'SOLAR_WITH_SHADOWS', True)
flat_threshold = getattr(settings, 'SOLAR_FLAT_THRESHOLD', 5)
optimal_azimuth = getattr(settings, 'SOLAR_OPTIMAL_AZIMUTH', 180)
optimal_tilt = getattr(settings, 'SOLAR_OPTIMAL_TILT', 40)

print('sample_rate: {}'.format(sample_rate))
print('with_shadows: {}'.format(with_shadows))

STATUS_TODO = 0
STATUS_PENDING = 1
STATUS_DONE = 2
STATUS_FAILED = 3


def round5(f):
    mul = f // 5
    if f % 5 > 2.5:
        mul += 1
    return mul * 5


def compute_radiation(exposed_area, tim, triangle):
    azimuth = triangle.azimuth
    tilt = triangle.tilt
    # here we special case "flat" roofs
    if tilt <= flat_threshold:
        azimuth = optimal_azimuth
        tilt = optimal_tilt

    rdiso_flat, rdiso = get_rdiso5(round5(azimuth), round5(tilt))
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
        azimuth,
        tilt,
        28,  # Meteonorm 7 Output Preview for Bruxelles centre
        1,
        month,
        tmy_index,
        rdiso_flat,
        rdiso)

    diffuse = triangle.area * (radiation_global - radiation_direct)
    direct = exposed_area * radiation_direct

    return (diffuse + direct) * sample_rate


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
    time_and_vec = []
    for ti in day:
        sunpos = get_sun_position(tr.center, ti)
        sunvec = unit_vector(
            get_coords_from_angles(tr.center, sunpos.elevation, sunpos.azimuth)
            - tr.center)
        time_and_vec.append((ti, sunvec))

    def chain(db, executor):
        rad = 0
        if with_shadows:
            get_intersections = lambda tv: query_intersections(db, tr.geom, tv[1])
            for (ti, sunvec), row_intersect in zip(
                    time_and_vec, executor.map(get_intersections,
                                               time_and_vec)):
                exposed_area = get_exposed_area(tr, sunvec, row_intersect)
                rad += compute_radiation(exposed_area, ti, tr)

        else:
            for ti in day:
                rad += compute_radiation(tr.area, ti, tr)

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


def compute_radiation_for_roof_batch(row):
    id = row[0]
    geom = row[1]
    area = get_roof_area(geom)
    start_time = now()
    db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES, reset=True)
    db.exec('insert_result',
            (0.0, area, STATUS_PENDING, start_time, start_time, id))
    try:
        with ThreadPoolExecutor() as executor:
            total_rad = sum(process_tasks(geom, db, executor))

        db.exec('insert_result',
                (total_rad, area, STATUS_DONE, start_time, now(), id))
        return id, STATUS_DONE
    except Exception as ex:
        logger.error('Error:compute({})\n{}'.format(type(ex), ex))
        db.exec('insert_result',
                (0.0, area, STATUS_FAILED, start_time, now(), id))
        return id, STATUS_FAILED


def compute_batches(batch_size):
    db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    with ProcessPoolExecutor() as executor:
        while True:
            rows = list(
                rows_with_geom(db, 'select_result_batch', (batch_size, ), 1))
            if 0 == len(rows):
                break
            for _ in executor.map(
                    compute_radiation_for_roof_batch, rows, chunksize=4):
                pass
