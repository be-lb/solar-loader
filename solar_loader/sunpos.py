import numpy as np
from pysolar import solar
from pyproj import Proj, transform
from .records import SunPosition
from .geom import vec2_dist

l72 = Proj(init='EPSG:31370')
wgs = Proj(init='EPSG:4326')


class SunposNight(Exception):
    pass


def sub(a, b):
    return a - b


def add(a, b):
    return a + b


def get_sun_position(ref_point, tim):
    """Get sun position for reference point and time at 1 degree's distance reprojected on l72

    ref_point -- a 3d vector in Lambert72
    tim       -- a datetime

    returns a records.SunPosition
    """
    px, py, pz = ref_point
    lon, lat, z = transform(l72, wgs, px, py, pz)
    azimut = solar.get_azimuth(lat, lon, tim, z)
    altitude = solar.get_altitude(lat, lon, tim, z)
    a = 180 - azimut
    elev = altitude
    if a > 270:
        o = a - 270
        # q = 4
        op_x = sub
        op_y = add
    elif a > 180:
        o = 90 - (a - 180)
        # q = 3
        op_x = sub
        op_y = sub
    elif a > 90:
        o = a - 90
        # q = 2
        op_x = add
        op_y = sub
    else:
        o = 90 - a
        # q = 1
        op_x = add
        op_y = add

    if elev < 1:
        return SunPosition([0, 0, 0], 0, 0, False, tim, 0, 0)

    r = np.deg2rad(o)
    s = np.sin(r)
    c = np.cos(r)
    e = np.sin(np.deg2rad(elev))
    united_coords = [op_x(lon, c), op_y(lat, s)]
    l72_coords = transform(wgs, l72, *united_coords)
    dist = vec2_dist([px, py], l72_coords)
    sun_e = e * dist
    sun_pos = np.array([l72_coords[0], l72_coords[1], sun_e])

    return SunPosition(sun_pos, o, elev, True, tim, 90 - altitude, azimut)
