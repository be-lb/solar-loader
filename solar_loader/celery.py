import itertools as it
from celery import Celery, chain, chord, group, Task
from psycopg2.extensions import AsIs
import django
from django.conf import settings
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from .store import Data
from .tmy import TMY
from .records import GisTriangle, Triangle
from .time import generate_sample_times
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
from .compute import get_exposed_area
from .rdiso import get_rdiso5
from .radiation import compute_gk
from .rad5 import rad5

django.setup()
SAMPLE_RATE = 7 * 4 * 2
db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)

with_shadows = getattr(settings, 'SOLAR_WITH_SHADOWS', False)

app = Celery('solar')
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['pickle']
app.conf.result_backend = 'redis://'


def round5(f):
    mul = f // 5
    if f % 5 > 2.5:
        mul += 1
    return mul * 5


@app.task(ignore_result=False)
def tsum(numbers):
    return sum(numbers)


@app.task(ignore_result=False)
def query_store(roof_id, rad):
    db.exec('insert_result', (roof_id, rad))


@app.task(ignore_result=False)
def compute_radiation(exposed_area, tim, triangle):
    return rad5(round5(triangle.tilt), round5(
        triangle.azimuth)) * triangle.area
    # rdiso_flat, rdiso = get_rdiso5(
    #     round5(triangle.azimuth), round5(triangle.tilt))
    # gh = tmy.get_float('G_Gh', tim)
    # dh = tmy.get_float('G_Dh', tim)
    # hs = tmy.get_float('hs', tim)
    # Az = tmy.get_float('Az', tim)
    # month = tim.month
    # tmy_index = tmy.get_index(tim)

    # radiation_global, radiation_direct = compute_gk(
    #     gh,
    #     dh,
    #     90.0 - hs,
    #     Az,
    #     0.2,
    #     triangle.azimuth,
    #     triangle.tilt,
    #     28,  # Meteonorm 7 Output Preview for Bruxelles centre
    #     1,
    #     month,
    #     tmy_index,
    #     rdiso_flat,
    #     rdiso)

    # diffuse = triangle.area * (radiation_global - radiation_global)
    # direct = exposed_area * radiation_direct

    # return diffuse + direct


@app.task(ignore_result=False)
def compute_exposed_area(row_intersect, triangle, sunvec):
    # print('compute_exposed_area({}, {}, {})'.format(triangle, sunvec,
    #                                                 row_intersect))
    return get_exposed_area(triangle, sunvec, row_intersect)


@app.task(ignore_result=False)
def query_intersections(triangle, sunvec):
    nearvec = sunvec * 1.0
    farvec = sunvec * 200.0
    triangle_near = Triangle(triangle.a + nearvec, triangle.b + nearvec,
                             triangle.c + nearvec)
    triangle_far = Triangle(triangle.a + farvec, triangle.b + farvec,
                            triangle.c + farvec)
    polyhedr = make_polyhedral(triangle_near, triangle_far)

    return list(rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ), 1))


def make_chain_with_shadows(ti, tr):
    sunpos = get_sun_position(tr.center, ti)
    sunvec = unit_vector(
        get_coords_from_angles(tr.center, sunpos.elevation, sunpos.azimuth) -
        tr.center)
    return (query_intersections.s(tr.geom, sunvec)
            | compute_exposed_area.s(tr, sunvec)
            | compute_radiation.s(ti, tr))


def make_chain_without_shadows(ti, tr):
    return compute_radiation.s(tr.area, ti, tr)


def prepare_task(roof_geometry):
    triangles = []
    times = generate_sample_times(SAMPLE_RATE)
    for geom in tesselate(roof_geometry):
        triangles.append(
            GisTriangle(
                geom,
                get_triangle_azimut(geom),
                get_triangle_inclination(geom),
                get_triangle_center(geom),
                get_triangle_area(geom),
            ))

    if with_shadows:
        return chord(
            make_chain_with_shadows(ti, tr)
            for ti, tr in it.product(times, triangles))

    return chord(
        make_chain_without_shadows(ti, tr)
        for ti, tr in it.product(times, triangles))


def compute_radiation_for_roof_direc(roof_geometry):
    triangles = []
    # times = generate_sample_times(SAMPLE_RATE)
    for geom in tesselate(roof_geometry):
        triangles.append(
            GisTriangle(
                geom,
                get_triangle_azimut(geom),
                get_triangle_inclination(geom),
                get_triangle_center(geom),
                get_triangle_area(geom),
            ))

    rads = map(
        lambda t: rad5(round5(t.tilt), round5(t.azimuth)) * t.area,
        triangles,
    )

    return sum(rads)


def compute_radiation_for_roof(roof_geometry):
    t = prepare_task(roof_geometry)
    return t(tsum.s()).get()


def compute_radiation_for_parcel(capakey):
    for row in rows_with_geom(db, 'select_roof_within', (capakey, ), 1):
        start = perf_counter()
        geom = row[1]
        print('roof({}) => {} ({})'.format(row[0],
                                           compute_radiation_for_roof(geom),
                                           perf_counter() - start))


def process_roof_row(row):
    geom = row[1]
    rad = compute_radiation_for_roof_direc(geom)
    roof_id = row[0]
    return roof_id, rad


def insert_result(r):
    db.exec('insert_result', r)
    return r[0]


def compute_for_all():
    db.exec('create_result')

    dones = []
    with ProcessPoolExecutor() as executor:
        rows = rows_with_geom(db, 'select_roof_all', (), 1)
        for roof_id, rad in executor.map(process_roof_row, rows, chunksize=4):
            print('{}'.format(len(dones)))
            dones.append((roof_id, rad))

    with ThreadPoolExecutor() as executor:
        for i in executor.map(insert_result, dones):
            print('inserted {}'.format(i))
