import math
import numpy as np
from shapely import geometry, wkb, wkt
from django.conf import settings
from .geom import tesselate

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
            row[geom_index] = wkt.loads(row[geom_index])
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


# def sort_point_clockwise(pts):


def triangles_to_surface(ts):
    return [triangle_to_wkt(t.a, t.b, t.c) for t in ts]


def triangles_to_surface_cc(ts):
    return [triangle_to_wkt(t.a, t.c, t.b) for t in ts]


def make_polyhedral_p(p0, p1):
    cs0 = p0.exterior.coords
    cs1 = p1.exterior.coords
    assert len(cs0) == len(
        cs1), 'Cannot join polygons with different length in a polyhedral'

    ts0 = tesselate(p0)
    ts1 = tesselate(p1)

    # hs = [polycoords_to_wkt(cs0)]
    hs = triangles_to_surface(ts0)
    for i, _ in enumerate(cs0):
        if i + 1 < len(cs0):
            a = cs0[i]
            b = cs1[i]
            c = cs1[i + 1]
            d = cs0[i + 1]
            hs.append(quad_to_wkt(a, b, c, d))

    # hs.append(polycoords_to_wkt(list(reversed(cs1))))
    hs.extend(triangles_to_surface_cc(ts1))

    return 'ST_GeomFromText(\'POLYHEDRALSURFACE Z({})\', 31370)'.format(
        ', '.join(hs))


def shape_to_obj(shape):
    return geometry.mapping(shape)


def shape_to_feature(shape, props=dict()):
    return {
        "type": "Feature",
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