from .geom import get_triangle_normal, get_triangle_center, get_triangle_area,\
    angle_between
import numpy as np
from click import secho
import math


def round5(f):
    mul = f // 5
    if f % 5 > 2.5:
        mul += 1
    return mul * 5


class GISTriangle:
    def __init__(self, geom, id=0, parcel_id=0):
        self.id = id
        self.parcel_id = parcel_id
        self.geom = geom  # the geometry of the triangle
        self.center = get_triangle_center(geom)
        self.area = get_triangle_area(geom)
        self.norm = None
        self.azimuth = None
        self.azimuth5 = None
        self.inclination = None
        self.inclination5 = None
        self.radiations = []
        self.rdiso_flat = None
        self.rdiso = None

    def init(self, db):
        # compute norm
        self.norm = get_triangle_normal(self.geom)
        self._compute_azimuth()
        self._compute_inclination()
        self._compute_rdiso_rdiso_flat(db)

    def get_norm(self):
        # if self.norm is None:
        #     self.norm = get_triangle_normal(self.geom)
        return self.norm

    def _compute_azimuth(self):
        norm = self.get_norm()

        if norm[0] == 0 and norm[1] == 0:
            self.azimuth = math.pi / 2
        else:
            self.azimuth = np.rad2deg(
                angle_between(np.array([0, 1]), norm[:2]))
        self.azimuth5 = round5(self.azimuth)

    def get_azimuth5(self):
        # if self.azimuth5 is None:
        #     self._compute_azimuth()
        return self.azimuth5

    def get_azimuth(self):
        # if self.azimuth is None:
        #     self._compute_azimuth()
        return self.azimuth

    def _compute_inclination(self):
        norm = self.get_norm()

        if norm[0] == 0 and norm[1] == 0:
            self.inclination = 0
        else:
            self.inclination = np.rad2deg(
                angle_between(np.array([norm[0], norm[1], 0]), norm))
        self.inclination5 = round5(self.inclination)

    def get_inclination(self):
        # if self.inclination is None:
        #    self._compute_inclination()
        return self.inclination

    def get_inclination5(self):
        # if self.inclination5 is None:
        #    self._compute_inclination()
        return self.inclination5

    def _compute_rdiso_rdiso_flat(self, db):
        res_roof_rdiso_rows = db.rows(
            'select_res_roof_rdiso',
            {},
            (self.get_azimuth5(), self.get_inclination5()),
        )

        res_roof_rdiso_rows = list(res_roof_rdiso_rows)
        if len(res_roof_rdiso_rows) == 0:
            secho('Missing entry for {} {} in res_roof_rdiso_rows'.format(
                self.get_azimuth5(), self.get_inclination5()))
        else:
            self.rdiso_flat = float(res_roof_rdiso_rows[0][0])
            self.rdiso = float(res_roof_rdiso_rows[0][1])

    def get_rdiso_flat(self):
        # if self.rdiso_flat is None:
        #    self._compute_rdiso_rdiso_flat(db)
        return self.rdiso_flat

    def get_rdiso(self):
        # if self.rdiso is None:
        #    self._compute_rdiso_rdiso_flat(db)
        return self.rdiso
