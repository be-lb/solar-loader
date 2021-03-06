import math
from functools import partial
import numpy as np
from shapely import geometry, ops
from .records import Triangle
from .earcut import earcut

# from scipy.spatial.transform import Rotation


class GeometryError(Exception):
    pass


class GeometryMissingDimension(GeometryError):
    pass


np_axis = {
    'x': np.array([1, 0, 0]),
    'y': np.array([0, 1, 0]),
    'z': np.array([0, 0, 1]),
}


def vec2_dist(a, b):
    """returns the distance between 2d vectors"""
    xs = b[0] - a[0]
    ys = b[1] - a[1]
    return math.sqrt(xs**2 + ys**2)


def vec_dist(p, q):
    """
    returns the distance between numpy vectors (used for testing)
    """
    return math.sqrt(np.sum(np.square(p - q)))


def translation_matrix(x, y, z):
    m = np.identity(4)
    m[3][0] = x
    m[3][1] = y
    m[3][2] = z
    return m


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis_unit = unit_vector(axis)
    a = math.cos(theta / 2.0)
    b, c, d = -axis_unit * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([
        [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac), 0],
        [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab), 0],
        [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc, 0],
        [0, 0, 0, 1],
    ])


def get_triangle_normal(t):
    """A normal vector for a given Triangle t
    ( see https://en.wikipedia.org/wiki/Cross_product )
    """
    a = np.cross(
        t.b - t.a,
        t.c - t.b,
    )

    if a[2] < 0:
        a = a * -1

    return a


def get_triangle_azimut(t):
    """
    The triangle azimut for a given Triange t,
    in degrees, from North, clockwise.
    """
    norm = get_triangle_normal(t)

    if norm[0] == 0 and norm[1] == 0:
        return np.rad2deg(math.pi / 2)
    else:
        return 360.0 - np.rad2deg(angle_between(np.array([0, 1]), norm[:2]))


def get_triangle_inclination(t):
    """
    Return the tilt (or inclination) of the triangle
    """
    norm = get_triangle_normal(t)

    if norm[0] == 0 and norm[1] == 0:
        return 0
    else:
        ret = np.rad2deg(angle_between(np.array([0, 0, 1]), norm))
        if ret > 90:
            return 360 - ret
        else:
            return ret


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
    # return Triangle(
    #     np.dot(t.a, m),
    #     np.dot(t.b, m),
    #     np.dot(t.c, m),
    # )
    return Triangle(
        np.dot([t.a[0], t.a[1], t.a[2], 1], m)[:3],
        np.dot([t.b[0], t.b[1], t.b[2], 1], m)[:3],
        np.dot([t.c[0], t.c[1], t.c[2], 1], m)[:3],
    )


def transform_polygon(m, poly):
    return geometry.Polygon([
        np.dot([coord[0], coord[1], coord[2], 1], m)[:3]
        for coord in poly.exterior.coords
    ])


def transform_multipolygon(m, mpoly):
    return geometry.MultiPolygon(map(partial(transform_polygon, m), mpoly))


def polygon_drop_z(poly):
    return geometry.Polygon([coord[:2] for coord in poly.exterior.coords])


def multipolygon_drop_z(mpoly):
    return geometry.MultiPolygon(map(polygon_drop_z, mpoly))


def triangle_from_shape(shape):
    coords = shape.exterior.coords
    return Triangle(
        np.array(coords[0]), np.array(coords[1]), np.array(coords[2]))


# RET = rotation_matrix([1, 0, 0], np.deg2rad(45)) @ rotation_matrix([0, 1, 0], np.deg2rad(45)) 


def tesselate(shape):
    """
    shape -- shapely.geometry.Geometry
    
    returns a list of triangles
    """
    triangles = [s for s in ops.triangulate(shape)]
    if 0 == len(triangles):
        triangles = [transform_polygon(IRET, s) for s in ops.triangulate(transform_multipolygon(RET, shape))]
    contained_triangles = filter(
        lambda s: shape.contains(geometry.Point(get_triangle_center(triangle_from_shape(s)))),
        triangles)
    return [triangle_from_shape(s) for s in triangles]


def get_flattening_mat(vec, translate=None):
    """
    Given a coordinates vector of 3 dimensions, this function
    will return a matrix that operates 2 rotations in order to
    align the said vector with (0,0,1)
    """
    dist = np.linalg.norm(vec)
    if abs(dist) > 0:
        nt = vec / dist
        pdist = vec2_dist(np.array([0, 0]), np.array([nt[0], nt[1]]))
        az = math.atan2(nt[1], nt[0])
        el = np.deg2rad(90) - math.atan2(nt[2], pdist)
        raz = rotation_matrix([0, 0, 1], az)
        rel = rotation_matrix([0, 1, 0], el)
        # m = np.dot(raz, rel)
        if translate is not None:
            return translate @ raz @ rel
        return raz @ rel

    raise GeometryMissingDimension('{}, {}'.format(nt, dist))


def get_triangle_flat_mat(t):
    """returns a flatening matrix for a triangle"""

    return get_flattening_mat(get_triangle_normal(t))


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)
    
    
def tesselate_earcut(coords, ctor):

    vertices = []
    for c in coords:
        vertices.append(c[0])
        vertices.append(c[1])
        vertices.append(c[2])
    
    index = earcut(vertices, dim=3)
    
    triangles = []
    for i in range(0, len(index), 3):
        ia = index[i] * 3
        ib = index[i + 1] * 3
        ic = index[i + 2] * 3
        a = [vertices[ia],vertices[ia+1],vertices[ia+2]]
        b = [vertices[ib],vertices[ib+1],vertices[ib+2]]
        c = [vertices[ic],vertices[ic+1],vertices[ic+2]]
        triangles.append(ctor(a,b,c))
        
    return triangles
        
def ctor_triangle(a, b , c):
    return Triangle(np.array(a),np.array(b),np.array(c))

def ctor_polygon(a, b, c):
    return geometry.Polygon([a,b,c,a])



# from https://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python/13849249#13849249
def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'"""
    v1 = np.array(v1)
    v2 = np.array(v2)

    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)

    dot_v1u_v2u = np.dot(v1_u, v2_u)
    cross_v1_v2 = np.cross(v1, v2)

    arccos = np.arccos(np.clip(dot_v1u_v2u, -1.0, 1.0))

    if cross_v1_v2.ndim == 0:
        if cross_v1_v2 >= 0:
            return arccos
        else:
            return (2 * math.pi) - arccos
    elif arccos == 0:
        return arccos
    for axis in ['z', 'y', 'z']:
        dot_with_axis = np.dot(cross_v1_v2, np_axis[axis])
        if dot_with_axis > 0:
            return arccos
        elif dot_with_axis < 0:
            return (2 * math.pi) - arccos
    return arccos



RET = rotation_matrix([1, 0, 0], np.deg2rad(45)) #@ rotation_matrix([0, 1, 0], np.deg2rad(45))
IRET = np.linalg.inv(RET)

