import numpy as np
from pysolar import solar
from pyproj import Proj, transform
from pytz import utc

from .records import SunPosition
from .geom import vec2_dist

l72 = Proj(init='EPSG:31370')
wgs = Proj(init='EPSG:4326')


def _get_coords_from_angles(ref_point, elev, azimut, dist=10000):
    px, py, pz = ref_point

    x = px + (dist * np.sin(azimut))
    y = py + (dist * np.cos(azimut))
    z = pz + (dist * np.sin(elev))

    return np.array([x, y, z])


def get_sun_position(ref_point, tim):
    """Get sun position for reference point and time at 1 degree's distance
    reprojected on l72

    ref_point -- a 3d vector in Lambert72
    tim       -- a datetime

    returns a records.SunPosition
    """
    utc_time = tim.astimezone(utc)
    px, py, pz = ref_point
    lon, lat, z = transform(l72, wgs, px, py, pz)

    azimut = solar.get_azimuth(lat, lon, utc_time, z)
    altitude = solar.get_altitude(lat, lon, utc_time, z)
    elev = altitude
    aa = abs(azimut)
    saa = aa if aa < 180 else aa - 360

    if elev < 1:
        return SunPosition([0, 0, 0], 0, 0, False, tim, 0, 0)

    coords = _get_coords_from_angles(ref_point, np.deg2rad(elev),
                                     np.deg2rad(saa + 180))
    return SunPosition(coords, saa + 180, elev, True, tim, 90 - altitude, saa)
