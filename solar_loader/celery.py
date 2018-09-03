import itertools as it
from celery import Celery, chain, chord, group
from psycopg2.extensions import AsIs
import django
from django.conf import settings

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

django.setup()
SAMPLE_RATE = 14
db = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)
app = Celery('solar')
app.conf.task_serializer = 'pickle'
app.conf.result_serializer = 'pickle'
app.conf.accept_content = ['pickle']


def round5(f):
    mul = f // 5
    if f % 5 > 2.5:
        mul += 1
    return mul * 5


@app.task(ignore_result=False)
def tsum(numbers):
    return sum(numbers)


@app.task(ignore_result=False)
def compute_radiation(tim, triangle, exposed_area):
    rdiso_flat, rdiso = get_rdiso5(
        round5(triangle.azimuth), round5(triangle.tilt))
    gh = tmy.get_float('G_Gh', tim)
    dh = tmy.get_float('G_Dh', tim)
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

    diffuse = triangle.area * (radiation_global - radiation_global)
    direct = exposed_area * radiation_direct

    return diffuse + direct


@app.task(ignore_result=False)
def compute_exposed_area(triangle, sunvec, row_intersect):
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


def make_chain(ti, tr):
    sunpos = get_sun_position(tr.center, ti)
    sunvec = unit_vector(
        get_coords_from_angles(tr.center, sunpos.elevation, sunpos.azimuth) -
        tr.center)
    return (query_intersections.s(tr.geom, sunvec)
            | compute_exposed_area.s(tr, sunvec)
            | compute_radiation.s(ti, tr))


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

    batch = chord(
        make_chain(ti, tr) for ti, tr in it.product(times, triangles))

    return batch


def compute_radiation_for_roof(roof_geometry):
    t = prepare_task(roof_geometry)
    return t(tsum.s()).get()


def compute_radiation_for_parcel(capakey):
    for row in rows_with_geom(db, 'select_roof_within', (capakey, ), 1):
        geom = row[1]
        print('roof({}) => {}'.format(row[0],
                                      compute_radiation_for_roof(geom)))
