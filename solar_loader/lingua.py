from shapely import geometry, wkb, wkt
from django.conf import settings

# to say if we use wkb or wkt to communicate with the db
use_wkb = True
if hasattr(settings, 'SOLAR_WKT_FROM_DB') and settings.SOLAR_WKT_FROM_DB:
    use_wkb = False


def rows_with_geom(db, select, params, geom_index):
    if use_wkb:
        for row in db.rows(select, {'conv_geom_operator': ''}, params):
            row = list(row)
            row[geom_index] = wkb.loads(row[geom_index], hex=True)
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


def shape_to_obj(shape):
    return geometry.mapping(shape)


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