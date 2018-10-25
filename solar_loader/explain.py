import itertools as it
from functools import partial
import logging
from psycopg2.extensions import AsIs
import django
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
from time import perf_counter
import shapely

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
    get_triangle_normal,
    tesselate,
    unit_vector,
    transform_polygon,
    transform_triangle,
)
from .sunpos import get_sun_position
from .lingua import make_polyhedral, rows_with_geom, triangle_to_wkt, tesselate_to_shape
from .compute import get_exposed_area, get_roof_area
from .rdiso import get_rdiso5
from .radiation import compute_gk

logger = logging.getLogger(__name__)

django.setup()
tmy = TMY(settings.SOLAR_TMY)
db = Data(
    settings.SOLAR_CONNECTION,
    settings.SOLAR_TABLES,
)

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
STATUS_ACK = 4


def round5(f):
    mul = f // 5
    if f % 5 > 2.5:
        mul += 1
    return mul * 5


class Result:
    def __init__(self):
        self.tid = 1
        self.triangles = []
        self.shadows = []
        self.shadowers = []
        self.sunvecs = []

    def get_id(self):
        i = self.tid
        self.tid += 1
        return i

    def insert_triangle(self, h, exposed, geom):
        tid = self.get_id()
        self.triangles.append((
            tid,
            h,
            exposed,
            geom,
        ))
        return tid

    def insert_shadow(self, hour, stype, geom):
        self.shadows.append((
            hour,
            stype,
            geom,
        ))

    def insert_shadower(self, tid, sid):
        self.shadowers.append((
            tid,
            sid,
        ))

    def commit(self):
        for tid, h, exposed, geom in self.triangles:
            geom_wkt = 'ST_GeomFromText(\'POLYGON Z{}\', 31370)'.format(
                triangle_to_wkt(
                    geom.a,
                    geom.b,
                    geom.c,
                ))
            row = (tid, h, exposed, AsIs(geom_wkt))
            db.exec('insert_explain_triangle', row)

        for hour, stype, geom in self.shadows:
            geom_wkt = 'ST_GeomFromText(\'{}\', 31370)'.format(geom.wkt)
            # print(geom_wkt)
            row = (hour, stype, AsIs(geom_wkt))
            db.exec('insert_explain_shadow', row)

        for row in self.shadowers:
            db.exec('insert_explain_shadower', row)


result = Result()


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

    diffuse = radiation_global - radiation_direct
    direct = exposed_area * radiation_direct

    # print('  diffuse: {}'.format(diffuse))
    # print('  direct:  {}'.format(direct))

    # return (diffuse + direct) * sample_rate
    return diffuse, direct


class IntersectCache:
    def __init__(self):
        self._cache = dict()

    def get_solid(self, row):
        id = row[0]
        if id not in self._cache:
            tes = tesselate_to_shape(row[1])
            print('IntersectCache INSERT {} {}'.format(id, len(tes)))
            self._cache[id] = tes # tesselate_to_shape(row[1])
        return (id, self._cache[id])
    
    def dump_cache(self):
        for id in self._cache:
            c= self._cache[id]
            for geom in c:
                db.exec('insert_tesselated', (id, AsIs('ST_GeomFromText(\'{}\', 31370)'.format(geom.wkt))))

intersect_cache = IntersectCache()


def query_intersections(triangle, sunvec, hour):
    nearvec = sunvec * 0.1
    farvec = sunvec * 200.0
    triangle_near = Triangle(triangle.a + nearvec, triangle.b + nearvec,
                             triangle.c + nearvec)
    triangle_far = Triangle(triangle.a + farvec, triangle.b + farvec,
                            triangle.c + farvec)
    polyhedr = make_polyhedral(triangle_near, triangle_far)

    start = perf_counter()
    select = rows_with_geom(db, 'select_intersect', (AsIs(polyhedr), ), 1)
    results = list(map(lambda row: intersect_cache.get_solid(row), select))

    db.exec(
        'insert_polyhedral',
        (
            hour,
            # db.explain('select_intersect', (AsIs(polyhedr), )),
            str(perf_counter() - start),
            AsIs(polyhedr),
        ))

    return results


def make_task(day, tr):
    time_and_vec = []
    for ti in day:
        sunpos = get_sun_position(tr.center, ti)
        if sunpos.is_daylight:
            sunvec = unit_vector(sunpos.coords - tr.center)
            time_and_vec.append((ti, sunvec))

    get_intersections = lambda tv: query_intersections(tr.geom, tv[1], tv[0].hour)
    its = list(map(get_intersections, time_and_vec))

    hours = []
    sunvecs = []
    exposed = []
    diffuse = []
    direct = []
    tot = []

    for (ti, sunvec), row_intersect in zip(time_and_vec, its):

        def pp(t, trans_mat, rot_mat, geom):
            flat_mat = trans_mat @ rot_mat
            # unrot_mat = np.linalg.inv(rot_mat)
            unflat_mat = np.linalg.inv(flat_mat)
            flat_triangle = transform_triangle(flat_mat, tr.geom)

            if 'append' == t:

                def get_z(x, y):
                    rp = np.dot([x, y, 0, 1], rot_mat)
                    return rp[2]

                g = shapely.geometry.Polygon([
                    [coord[0], coord[1], 0]
                    #   get_z(coord[0], coord[1])]
                    for coord in geom.exterior.coords
                ])

                moeg = transform_polygon(unflat_mat, g)
                result.insert_shadow(ti.hour, 'unflat', moeg)
                result.insert_shadow(ti.hour, 'flat', g)
                result.insert_shadow(
                    ti.hour, 'ref',
                    shapely.geometry.Polygon([
                        flat_triangle.a[:3],
                        flat_triangle.b[:3],
                        flat_triangle.c[:3],
                        flat_triangle.a[:3],
                    ]))
            elif 'solid' == t:
                result.insert_shadow(ti.hour, 'solid', geom)

        exposed_area = get_exposed_area(
            tr, sunvec, (map(lambda r: r[1], row_intersect)), pp)

        di, dr = compute_radiation(exposed_area, ti, tr)
        hours.append(str(ti.hour))
        sunvecs.append('({:.1f}, {:.1f}, {:.1f})'.format(
            sunvec[0], sunvec[1], sunvec[2]))
        exposed.append('{:.2f}'.format(exposed_area))
        diffuse.append(str(round(di / 1000)))
        direct.append(str(round(dr / 1000)))
        tot.append(str(round((di + dr) / 1000)))

        tid = result.insert_triangle(ti.hour, exposed_area, tr.geom)
        for r in row_intersect:
            result.insert_shadower(tid, r[0])

    is_header = True
    for n, line in (
        ("hours", hours),
            # ("sunvec", sunvecs),
        ("exposed", exposed),
        ("diffuse", diffuse),
        ("direct", direct),
        ("tot", tot),
    ):
        print('{}\t|\t{}'.format(n, '\t| '.join(line)))
        if is_header:
            is_header = False
            sep = [' --- ' for _ in line]
            print('--- | --- | {}'.format('|'.join(sep)))


def format_triangle(t):
    s = []
    for v in (t.a, t.b, t.c):
        s.append('({:.2f}, {:.2f}, {:.2f})'.format(
            v[0],
            v[1],
            v[2],
        ))
    return ','.join(s)


def process_tasks(roof_geometry, day):

    for i, geom in enumerate(tesselate(roof_geometry)):
        t = GisTriangle(
            geom,
            get_triangle_azimut(geom),
            get_triangle_inclination(geom),
            get_triangle_center(geom),
            get_triangle_area(geom),
        )

        n = get_triangle_normal(t.geom)
        print('```')
        print('Triangle #{}'.format(i))
        print('Normal:    {}'.format(n / np.linalg.norm(n)))
        print('Azimuth:   {}'.format(t.azimuth))
        # print('test_case# [{}, {}, 0.01]'.format(
        #     format_triangle(t.geom), t.azimuth))
        print('Elevation: {}'.format(t.tilt))
        print('Area:      {}'.format(t.area))
        print('```')
        make_task(day, t)
        print()


def compute_radiation_roof(row, day):
    id = row[0]
    geom = row[1]
    area = get_roof_area(geom)

    # print('{} @ {}'.format(id, day))

    process_tasks(geom, day)


def analyze(roof_id, day):
    db.exec('create_explain')
    rows = list(rows_with_geom(db, 'select_roof', (roof_id, ), 1))

    compute_radiation_roof(rows[0], day)

    result.commit()
    intersect_cache.dump_cache()
