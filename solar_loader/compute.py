import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial

import numpy as np
from psycopg2.extensions import AsIs
from shapely import geometry, ops

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


def get_intersections_for_triangle(gis_triangle, sunvec, db):
    sunvecunit = unit_vector(sunvec)

    nearvec = sunvecunit * 1.0  # 0.1
    farvec = sunvecunit * 200.0

    triangle_near = Triangle(gis_triangle.geom.a + nearvec,
                             gis_triangle.geom.b + nearvec,
                             gis_triangle.geom.c + nearvec)
    triangle_far = Triangle(gis_triangle.geom.a + farvec,
                            gis_triangle.geom.b + farvec,
                            gis_triangle.geom.c + farvec)
    polyhedr = make_polyhedral(triangle_near, triangle_far)

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

    intersection = []

    for row in row_intersect:
        # get the geometry
        solid = row[1]
        # apply same transformation than the flatten triangle
        flatten_solid = transform_multipolygon(flat_mat, solid)

        for s in flatten_solid:
            try:
                it = triangle_2d.intersection(s)
                if it.geom_type == 'Polygon':
                    intersection.append(it)  # intersection.union(it)

            except Exception as exc:
                logger.debug(str(exc))

    if len(intersection) == 0:
        return gis_triangle.area
    else:
        int_area = ops.cascaded_union(intersection).area
        return gis_triangle.area - (
            int_area * gis_triangle.area / triangle_2d.area)


def worker(db, tmy, sample_rate, gis_triangles, with_shadows, day):
    alb = 0.2
    daily_radiations = []

    for tim in day:
        gh = tmy.get_float_average('G_Gh', tim, sample_rate)
        dh = tmy.get_float_average('G_Dh', tim, sample_rate)
        month = tim.month
        tmy_index = tmy.get_index(tim)
        hourly_radiations = []
        for gis_triangle in gis_triangles:
            with TimeCounter('triangle'):
                (center, sunpos, triangle_azimuth, triangle_inclination,
                 triangle_area, triangle_rdiso,
                 triangle_rdiso_flat) = init_triangle(tim, gis_triangle)

                if sunpos.is_daylight is False:
                    continue

                # vector from center of triangle to sun position
                sunvec = sunpos.coords - center

                # radiation
                with TimeCounter('radiations'):
                    radiation_global, radiation_direct = compute_gk(
                        gh, dh, sunpos.sza, sunpos.saa, alb, triangle_azimuth,
                        triangle_inclination, center[2], 1, month, tmy_index,
                        triangle_rdiso_flat, triangle_rdiso)

                    radiation_diffuse = radiation_global - radiation_direct

                if with_shadows:
                    with TimeCounter('shadows'):
                        direct_area = get_exposed_area(
                            gis_triangle, sunvec,
                            get_intersections_for_triangle(
                                gis_triangle, sunvec, db))
                else:
                    direct_area = triangle_area

                total_diffuse = triangle_area * radiation_diffuse
                total_direct = direct_area * radiation_direct

                gis_triangle.radiations.append(total_direct + total_diffuse)
                hourly_radiations.append(total_direct + total_diffuse)

        daily_radiations.append(np.sum(hourly_radiations))

    return np.sum(daily_radiations)


def get_results_roof(db, tmy, sample_rate, roof_id, with_shadows=False):

    days = generate_sample_days(sample_rate)
    roof = list(rows_with_geom(db, 'select_roof', (roof_id, ), 1))[0]
    gis_triangles = []
    print('roof({})'.format(roof_id))
    for t in tesselate(roof[1]):
        gis_t = GISTriangle(t)
        gis_t.init(db)
        gis_triangles.append(gis_t)

    radiations = []

    with TimeCounter('total'):
        with ThreadPoolExecutor() as executor:
            for daily_radiation in executor.map(
                    partial(worker, db, tmy, sample_rate, gis_triangles,
                            with_shadows), days):
                radiations.append(daily_radiation * float(sample_rate))

    features = []
    for t in gis_triangles:
        t.radiations = t.radiations * sample_rate
        features.append(triangle_to_geojson(t))

    return shape_to_feature(roof[1], roof_id,
                            dict(irradiance=np.sum(radiations), area=roof[2]))


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
