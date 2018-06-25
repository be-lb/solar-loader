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
