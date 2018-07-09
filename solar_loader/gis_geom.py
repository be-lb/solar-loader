from .geom import get_triangle_normal, get_triangle_center, get_triangle_area,\
    angle_between
import numpy as np


class GISTriangle:
    def __init__(self, geom):
        self.geom = geom  # the geometry of the triangle
        self.center = get_triangle_center(geom)
        self.area = get_triangle_area(geom)
        self.norm = None
        self.azimuth = None
        self.inclination = None

    def get_norm(self):
        if self.norm is None:
            self.norm = get_triangle_normal(self.geom)
        return self.norm

    def get_azimuth(self):
        if self.azimuth is None:
            norm = self.get_norm()
            self.azimuth = np.rad2deg(
                angle_between(np.array([0, 1]), norm[:2]))
        return self.azimuth

    def get_inclination(self):
        if self.inclination is None:
            norm = self.get_norm()
            self.inclination = np.rad2deg(
                angle_between(np.array([norm[0], norm[1], 0]), norm))
        return self.inclination
