import math
import logging
import numpy as np
from shapely import geometry, wkb, wkt, ops
from django.conf import settings
from .geom import tesselate, angle_between

logger = logging.getLogger(__name__)

# to say if we use wkb or wkt to communicate with the db
use_wkb = True
if hasattr(settings, 'SOLAR_WKT_FROM_DB') and settings.SOLAR_WKT_FROM_DB:
    use_wkb = False


def rows_with_geom(db, select, params, geom_index):
    if use_wkb:
        for row in db.rows(select, {'conv_geom_operator': ''}, params):
            row = list(row)
            try:
                row[geom_index] = wkb.loads(row[geom_index], hex=True)
            except Exception as exc:
                print('GEOM: {}'.format(row[geom_index]))
                raise exc
            yield row
    else:
        for row in db.rows(select, {'conv_geom_operator': 'st_astext'},
                           params):
            row = list(row)
            try:
                row[geom_index] = wkt.loads(row[geom_index])
            except Exception as ex:
                logger.error('could not read "{}"\n{}'.format(
                    row[geom_index], ex))
                continue
            yield row


def coord_to_wkt(c):
    return '{} {} {}'.format(*c)


def triangle_to_wkt(a, b, c):
    return '(({}))'.format(', '.join(map(coord_to_wkt, [
        a,
        b,
        c,
        a,
    ])))


def quad_to_wkt(a, b, c, d):
    return '(({}))'.format(', '.join(map(coord_to_wkt, [
        a,
        b,
        c,
        d,
        a,
    ])))


def polycoords_to_wkt(coords):
    return '(({}))'.format(', '.join(map(coord_to_wkt, coords)))


def make_polyhedral(t0, t1):
    hs = [
        triangle_to_wkt(t0.a, t0.b, t0.c),
        quad_to_wkt(t0.a, t1.a, t1.b, t0.b),
        quad_to_wkt(t0.b, t1.b, t1.c, t0.c),
        quad_to_wkt(t0.c, t1.c, t1.a, t0.a),
        triangle_to_wkt(t1.a, t1.c, t1.b),
    ]

    return 'ST_GeomFromText(\'POLYHEDRALSURFACE Z({})\', 31370)'.format(
        ', '.join(hs))


NOON = [0, 1]


def angle_from_noon(pt):
    return angle_between(NOON, [pt[0], pt[1]])


def sort_point_clockwise(pts):
    return sorted(pts, key=angle_from_noon)


def sort_point_counterclockwise(pts):
    return sorted(pts, key=angle_from_noon, reverse=True)


def triangle_to_wkt_cw(t):
    a, b, c = sort_point_clockwise([t.a, t.b, t.c])
    return triangle_to_wkt(a, b, c)


def triangle_to_wkt_ccw(t):
    a, b, c = sort_point_counterclockwise([t.a, t.b, t.c])
    return triangle_to_wkt(a, b, c)


def triangles_to_surface_cc(ts):
    # return [triangle_to_wkt(t.a, t.b, t.c) for t in ts]
    return map(triangle_to_wkt_cw, ts)


def triangles_to_surface_ccw(ts):
    # return [triangle_to_wkt(t.a, t.c, t.b) for t in ts]
    return map(triangle_to_wkt_ccw, ts)


def make_polyhedral_p_0(p0, p1):
    cs0 = p0.exterior.coords
    cs1 = p1.exterior.coords
    assert len(cs0) == len(
        cs1), 'Cannot join polygons with different length in a polyhedral'

    # ts0 = tesselate(p0)
    # ts1 = tesselate(p1)

    # hs = [polycoords_to_wkt(cs0)]
    # hs = list(triangles_to_surface_cc(ts0))
    hs = []
    for i, _ in enumerate(cs0):
        if i + 1 < len(cs0):
            a = cs0[i]
            b = cs1[i]
            c = cs1[i + 1]
            d = cs0[i + 1]
            # hs.append(quad_to_wkt(a, b, c, d))
            hs.append(triangle_to_wkt(a, b, c))
            hs.append(triangle_to_wkt(a, c, d))

    # hs.append(polycoords_to_wkt(list(reversed(cs1))))
    # hs.extend(triangles_to_surface_ccw(ts1))

    return 'ST_GeomFromText(\'POLYHEDRALSURFACE Z({})\', 31370)'.format(
        ', '.join(hs))


def make_polyhedral_p(p0, p1):
    cs0 = p0.exterior.coords
    cs1 = p1.exterior.coords
    assert len(cs0) == len(
        cs1), 'Cannot join polygons with different length in a polyhedral'

    polys = []
    for i, _ in enumerate(cs0):
        if i + 1 < len(cs0):
            a = cs0[i]
            b = cs1[i]
            c = cs1[i + 1]
            d = cs0[i + 1]
            polys.append(geometry.Polygon([a, b, c, d, a]))

    mp = geometry.MultiPolygon(polys)

    return 'ST_GeomFromText(\'{}\', 31370)'.format(mp.to_wkt())


def make_polyhedral_extrude(p0, x, y, z):
    ts0 = tesselate(p0)
    base = 'ST_GeomFromText(\'POLYHEDRALSURFACE Z({})\', 31370)'.format(
        ', '.join(triangles_to_surface_cc(ts0)))

    return 'ST_Extrude({}, {}, {}, {})'.format(base, x, y, z)


def shape_to_obj(shape):
    return geometry.mapping(shape)


def shape_to_feature(shape, id, props=dict()):
    return {
        "type": "Feature",
        "id": id,
        "geometry": shape_to_obj(shape),
        "properties": props,
    }


def make_feature(geom, props=dict()):
    return {
        "type": "Feature",
        "geometry": geom,
        "properties": props,
    }


def make_feature_collection(fs):
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:EPSG::31370"
            }
        },
        "features": fs,
    }


def triangle_to_geojson(t):
    return {
        'type': 'Feature',
        'properties': {
            'id':
            t.id,
            'parcel_id':
            t.parcel_id,
            'typology':
            '',
            'productivity':
            np.sum([t.radiations]),
            'area':
            t.area,
            'azimuth':
            t.get_azimuth()
            if t.get_azimuth() and not math.isnan(t.get_azimuth()) else 0,
            'tilt':
            t.get_inclination() if t.get_inclination()
            and not math.isnan(t.get_inclination()) else 0,
        },
        'geometry': {
            'type':
            'Polygon',
            'coordinates': [
                [
                    t.geom.a.tolist(),
                    t.geom.b.tolist(),
                    t.geom.c.tolist(),
                    t.geom.a.tolist(),
                ],
            ],
        }
    }