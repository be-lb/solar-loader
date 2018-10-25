import math
import logging
import numpy as np
from shapely import geometry, wkt
from .geom import tesselate, angle_between

logger = logging.getLogger(__name__)


def rows_with_geom(db, select, params, geom_index):
    for row in db.rows(select, {}, params):
        row = list(row)
        try:
            row[geom_index] = wkt.loads(row[geom_index])
        except Exception as ex:
            logger.error('could not read "{}"\n{}'.format(row[geom_index], ex))
            continue
        yield row


def coord_to_wkt(c):
    return '{:.2f} {:.2f} {:.2f}'.format(*c)


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


def make_polyhedral_bak(t0, t1):
    hs = [
        triangle_to_wkt(t0.a, t0.b, t0.c),
        quad_to_wkt(t0.a, t1.a, t1.b, t0.b),
        quad_to_wkt(t0.b, t1.b, t1.c, t0.c),
        quad_to_wkt(t0.c, t1.c, t1.a, t0.a),
        triangle_to_wkt(t1.a, t1.c, t1.b),
    ]

    return 'ST_GeomFromText(\'POLYHEDRALSURFACE Z({})\', 31370)'.format(
        ', '.join(hs))


def make_polyhedral(t0, t1):
    hs = [
        triangle_to_wkt(t0.a, t0.b, t0.c),
        # quad_to_wkt(t0.a, t1.a, t1.b, t0.b),
        triangle_to_wkt(t0.a, t1.a, t1.b),
        triangle_to_wkt(t0.a, t1.b, t0.b),
        #
        # quad_to_wkt(t0.b, t1.b, t1.c, t0.c),
        triangle_to_wkt(t0.b, t1.b, t1.c),
        triangle_to_wkt(t0.b, t1.c, t0.c),
        #
        # quad_to_wkt(t0.c, t1.c, t1.a, t0.a),
        triangle_to_wkt(t0.c, t1.c, t1.a),
        triangle_to_wkt(t0.c, t1.a, t0.a),
        #
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


def triangles_to_surface_cc(ts):
    # return [triangle_to_wkt(t.a, t.b, t.c) for t in ts]
    return map(triangle_to_wkt_cw, ts)


def shape_to_obj(shape):
    return geometry.mapping(shape)


def triangle_to_shape(t):
    return geometry.Polygon([
        t.a.tolist(),
        t.b.tolist(),
        t.c.tolist(),
        t.a.tolist(),
    ])


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


def tesselate_to_shape(shape):
    """
    shape -- shapely.geometry.Geometry
    
    returns a shapely.geometry.Multipolygon
    """
    return  list(map(triangle_to_shape, tesselate(shape)))
