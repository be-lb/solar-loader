import unittest
import numpy as np
from random import random
from functools import partial
from solar_loader import geom
from solar_loader.records import Triangle

SERIE_COUNT = 12


def get_rands(n, f):
    for i in range(SERIE_COUNT):
        r = []
        for i in range(n):
            r.append(random() * 1000.0)
        yield f(r)


class TestGeom(unittest.TestCase):
    def test_angle_between(self):
        self.assertEqual(
            geom.angle_between((1, 0, 0), (0, 1, 0)), 1.5707963267948966)
        self.assertEqual(geom.angle_between((1, 0, 0), (1, 0, 0)), 0.0)
        self.assertEqual(
            geom.angle_between((1, 0, 0), (-1, 0, 0)), 3.141592653589793)

    def test_flat_mat(self):
        r = partial(get_rands, 3, lambda r: np.array(r))
        for a, b, c in zip(r(), r(), r()):
            t = Triangle(a, b, c)
            m = geom.get_triangle_flat_mat(t)
            ft = geom.transform_triangle(m, t)
            self.assertAlmostEqual(ft.a[2], ft.b[2], delta=0.0000001)
            self.assertAlmostEqual(ft.a[2], ft.c[2], delta=0.0000001)


if __name__ == '__main__':
    unittest.main()
