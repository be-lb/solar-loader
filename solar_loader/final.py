import itertools as it
from functools import partial
import logging
from psycopg2.extensions import AsIs
import django
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import traceback

from .time import now
from .store import Data
from .tmy import TMY
from .records import GisTriangle, Triangle
from .time import generate_sample_days
from .geom import (
    get_triangle_area,
    get_triangle_azimut,
    get_triangle_center,
    get_triangle_inclination,
    tesselate,
    unit_vector,
)
from .sunpos import get_sun_position
from .lingua import make_polyhedral, rows_with_geom, tesselate_to_shape
from .compute import get_exposed_area, get_roof_area
from .rdiso import get_rdiso5
from .radiation import compute_gk

logger = logging.getLogger(__name__)

# django.setup()
tmy = TMY(settings.SOLAR_TMY)

sample_rate = getattr(settings, 'SOLAR_SAMPLE_RATE', 14)
with_shadows = getattr(settings, 'SOLAR_WITH_SHADOWS', True)
flat_threshold = getattr(settings, 'SOLAR_FLAT_THRESHOLD', 5)
flat_area_rate = getattr(settings, 'SOLAR_FLAT_AREA_RATE', 0.57)
optimal_azimuth = getattr(settings, 'SOLAR_OPTIMAL_AZIMUTH', 180)
optimal_tilt = getattr(settings, 'SOLAR_OPTIMAL_TILT', 40)

print('sample_rate: {}'.format(sample_rate))
print('with_shadows: {}'.format(with_shadows))

STATUS_TODO = 0
STATUS_PENDING = 1
STATUS_DONE = 2
STATUS_FAILED = 3
STATUS_ACK = 4

MAX_WORKERS = 32
TIMEOUT = 60


def round5(f):
    mul = f // 5
    if f % 5 > 2.5:
        mul += 1
    return mul * 5


def compute_radiation(exposed_rate, tim, triangle):
    azimuth = triangle.azimuth
    tilt = triangle.tilt

    is_flat = tilt <= flat_threshold

    if is_flat:
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

    diffuse = (radiation_global - radiation_direct)
    direct = exposed_rate * radiation_direct

    return (diffuse + direct) * sample_rate


class IntersectCache:
    def __init__(self):
        self._cache = dict()

    def get_solid(self, row):
        id = row[0]
        if id not in self._cache:
            self._cache[id] = tesselate_to_shape(row[1])
        return self._cache[id]


intersect_cache = IntersectCache()


def query_intersections(db, triangle, sunvec):
    nearvec = sunvec * 1.0
    farvec = sunvec * 200.0
    triangle_near = Triangle(triangle.a + nearvec, triangle.b + nearvec,
                             triangle.c + nearvec)
    triangle_far = Triangle(triangle.a + farvec, triangle.b + farvec,
                            triangle.c + farvec)
    polyhedr = make_polyhedral(triangle_near, triangle_far)

    select = rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ), 1)
    results = map(lambda row: intersect_cache.get_solid(row), select)
    return list(results)


def make_task(day, tr):
    time_and_vec = []
    for ti in day:
        sunpos = get_sun_position(tr.center, ti)
        sunvec = unit_vector(sunpos.coords - tr.center)
        time_and_vec.append((ti, sunvec))

    def chain(db, executor):
        rad = 0
        if tr.area > 0:
            if with_shadows:
                get_intersections = lambda tv: query_intersections(db, tr.geom, tv[1])
                for (ti, sunvec), row_intersect in zip(
                        time_and_vec,
                        executor.map(
                            get_intersections, time_and_vec, timeout=TIMEOUT)):
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
    tesselated = tesselate(roof_geometry)
    n = len(tesselated)
    if 0 == n:
        return 0
    for geom in tesselated:
        triangles.append(
            GisTriangle(
                geom,
                get_triangle_azimut(geom),
                get_triangle_inclination(geom),
                get_triangle_center(geom),
                get_triangle_area(geom),
            ))

    tasks = [make_task(day, tr) for day, tr in it.product(days, triangles)]

    return sum(map(lambda t: t(db, executor), tasks)) / n


def compute_radiation_roof(node_name, row):
    id = row[0]
    geom = row[1]
    area = get_roof_area(geom)
    start_time = now()
    db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES, reset=True)
    res = Data(
        settings.SOLAR_CONNECTION_RESULTS, settings.SOLAR_TABLES, reset=True)
    res.exec(
        'insert_result',
        (0.0, area, node_name, STATUS_PENDING, start_time, start_time, id))
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            total_rad = process_tasks(geom, db, executor)

        res.exec(
            'insert_result',
            (total_rad, area, node_name, STATUS_DONE, start_time, now(), id))
        return id, STATUS_DONE
    except ValueError as ex:
        logger.error('Value error in compute_radiation_roof : {}'.format(ex))
        res.exec('insert_result',
                 (0.0, area, node_name, STATUS_FAILED, start_time, now(), id))
        print(traceback.format_exc())
    except Exception as ex:
        logger.error('Exception in compute_radiation_roof : {}'.format(ex))
        res.exec('insert_result',
                 (0.0, area, node_name, STATUS_FAILED, start_time, now(), id))
        print(traceback.format_exc())


def compute_batches(node_name, batch_size):

    with ProcessPoolExecutor() as executor:
        while True:
            db = Data(
                settings.SOLAR_CONNECTION_RESULTS,
                settings.SOLAR_TABLES,
                reset=True,
            )

            rows = list(
                rows_with_geom(db, 'select_result_batch', (batch_size, ), 1))

            if 0 == len(rows):
                break

            rows_id = [str(row[0]) for row in rows]

            db.exec('insert_result_reservation',
                    (node_name, STATUS_ACK, rows_id))

            for _ in executor.map(
                    partial(compute_radiation_roof, node_name),
                    rows,
                    chunksize=4,
            ):
                pass
