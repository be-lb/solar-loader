import math
from functools import partial, reduce
import numpy as np
from shapely import geometry, ops
from .records import Triangle


class GeometryError(Exception):
    pass


class GeometryTypeError(GeometryError):
    def __init__(self, gt, expected=None):
        if expected is not None:
            self.message = 'Expected "{}", got "{}"'.format(expected, gt)
        else:
            self.message = '"{}" not supported'.format(gt)


class GeometryMissingDimension(GeometryError):
    pass


def vec2_dist(a, b):
    """returns the distance between 2d vectors"""
    xs = b[0] - a[0]
    ys = b[1] - a[1]
    return math.sqrt(xs**2 + ys**2)


def vec_dist(p, q):
    return math.sqrt(np.sum(np.square(p - q)))


def vec3_add(a, b):
    return [
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2],
    ]


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])


# def polygon_area(x, y):
#     correction = x[-1] * y[0] - y[-1] * x[0]
#     main_area = np.dot(x[:-1], y[1:]) - np.dot(y[:-1], x[1:])
#     return 0.5 * np.abs(main_area + correction)

# def get_triangle_area(pts):
#     return polygon_area(pts[:, 0], pts[:, 1])


def get_centroid(arr):
    length = arr.shape[0]
    sum_x = np.sum(arr[:, 0])
    sum_y = np.sum(arr[:, 1])
    return [sum_x / length, sum_y / length]


def get_triangle_normal(t):
    """returns normal vector of a records.Triangle

    see https://en.wikipedia.org/wiki/Cross_product
    """
    a = np.cross(
        t.b - t.a,
        t.c - t.a,
    )
    b = np.cross(
        t.b - t.a,
        t.c - t.a,
    )
    # simple check for highest z as we cannot assume triangles are always in the same direction
    if a[2] > b[2]:
        return a
    return b


def get_triangle_azimut(t):
    norm = get_triangle_normal(t)

    if norm[0] == 0 and norm[1] == 0:
        return math.pi / 2  # ???
    else:
        return np.rad2deg(angle_between(np.array([0, 1]), norm[:2]))


def get_triangle_inclination(t):
    norm = get_triangle_normal(t)

    if norm[0] == 0 and norm[1] == 0:
        return 0
    else:
        return np.rad2deg(angle_between(np.array([norm[0], norm[1], 0]), norm))


def get_triangle_center(t):
    return (t.a + t.b + t.c) / 3


def get_triangle_area(t):
    n = get_triangle_normal(t)
    n /= np.linalg.norm(n)
    products = [
        np.cross(t.a, t.b),
        np.cross(t.b, t.c),
        np.cross(t.c, t.a),
    ]
    total = np.sum(products, axis=0)
    result = np.dot(total, n)
    return abs(result / 2)


def transform_triangle(m, t):
    return Triangle(
        np.dot(t.a, m),
        np.dot(t.b, m),
        np.dot(t.c, m),
    )


def transform_polygon(m, poly):
    return geometry.Polygon(
        [np.dot(coord, m) for coord in poly.exterior.coords])


def transform_multipolygon(m, mpoly):
    return geometry.MultiPolygon(map(partial(transform_polygon, m), mpoly))


def polygon_drop_z(poly):
    return geometry.Polygon([coord[:2] for coord in poly.exterior.coords]), [
        coord[2] for coord in poly.exterior.coords
    ]


def polygon_add_z(poly, zs):
    return geometry.Polygon([(coord[0], coord[1], zs[i])
                             for i, coord in enumerate(poly.exterior.coords)])


def multipolygon_drop_z(mpoly):
    ps = []
    zs = []
    for p, z in map(polygon_drop_z, mpoly):
        ps.append(p)
        zs.append(z)

    return geometry.MultiPolygon(ps), zs


def triangle_from_shape(shape):
    coords = shape.exterior.coords
    return Triangle(
        np.array(coords[0]), np.array(coords[1]), np.array(coords[2]))


def tesselate(shape):
    """
    shape -- shapely.geometry.Geometry
    """
    triangles = [s for s in ops.triangulate(shape)]
    contained_triangles = filter(
        lambda s: shape.contains(geometry.Point(get_triangle_center(triangle_from_shape(s)))),
        triangles)
    return [triangle_from_shape(s) for s in contained_triangles]


def get_flattening_mat(vec):
    """
    Given a coordinates vector of 3 dimensions, this function
    will return a matrix 
    """
    dist = np.linalg.norm(vec)
    if abs(dist) > 0:
        nt = vec / dist
        pdist = vec2_dist(np.array([0, 0]), np.array([nt[0], nt[1]]))
        az = math.atan2(nt[1], nt[0])
        el = np.deg2rad(90) - math.atan2(nt[2], pdist)
        raz = rotation_matrix([0, 0, 1], az)
        rel = rotation_matrix([0, 1, 0], el)
        m = np.dot(raz, rel)
        return m

    raise GeometryMissingDimension('{}, {}'.format(nt, dist))


def get_triangle_flat_mat(t):
    """returns a flatening matrix for a triangle"""

    return get_flattening_mat(get_triangle_normal(t))


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)


# from https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python/13849249#13849249
def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

    >>> angle_between((1, 0, 0), (0, 1, 0))
    1.5707963267948966
    >>> angle_between((1, 0, 0), (1, 0, 0))
    0.0
    >>> angle_between((1, 0, 0), (-1, 0, 0))
    3.141592653589793
    """
    v1_u = unit_vector(np.array(v1))
    v2_u = unit_vector(np.array(v2))
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def foreach_coords(f):
    def inner(poly):
        for coord in poly.exterior.coords:
            f(coord)

    return inner


def reduce_coords(f, ini):
    def inner(poly):
        return reduce(f, poly.exterior.coords, ini)

    return inner


def op_coord(op, i, base, coord):
    return op(base, coord[i])


positive_infinity = float('inf')
negative_infinity = float('-inf')

poly_min_x = reduce_coords(partial(op_coord, min, 0), positive_infinity)
poly_min_y = reduce_coords(partial(op_coord, min, 1), positive_infinity)
poly_min_z = reduce_coords(partial(op_coord, min, 2), positive_infinity)
poly_max_x = reduce_coords(partial(op_coord, max, 0), negative_infinity)
poly_max_y = reduce_coords(partial(op_coord, max, 1), negative_infinity)
poly_max_z = reduce_coords(partial(op_coord, max, 2), negative_infinity)


def poly_bbox(poly):
    return (
        poly_min_x(poly),
        poly_min_y(poly),
        poly_min_z(poly),
        poly_max_x(poly),
        poly_max_y(poly),
        poly_max_z(poly),
    )


def multipoly_bbox(mp):
    return (
        reduce(lambda acc, poly: min(acc, poly_min_x(poly)), mp,
               positive_infinity),
        reduce(lambda acc, poly: min(acc, poly_min_y(poly)), mp,
               positive_infinity),
        reduce(lambda acc, poly: min(acc, poly_min_z(poly)), mp,
               positive_infinity),
        reduce(lambda acc, poly: max(acc, poly_max_x(poly)), mp,
               negative_infinity),
        reduce(lambda acc, poly: max(acc, poly_max_y(poly)), mp,
               negative_infinity),
        reduce(lambda acc, poly: max(acc, poly_max_z(poly)), mp,
               negative_infinity),
    )
