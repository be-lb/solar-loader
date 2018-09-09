import unittest
import numpy as np
from random import random
from functools import partial
from solar_loader import geom
from solar_loader.records import Triangle
import math

SERIE_COUNT = 12

angle_30 = math.pi / 6
angle_45 = math.pi / 4
angle_60 = math.pi / 3
angle_90 = math.pi / 2
angle_180 = math.pi


def get_rands(n, f):
    for i in range(SERIE_COUNT):
        r = []
        for i in range(n):
            r.append(random() * 1000.0)
        yield f(r)


class TestGeom(unittest.TestCase):
    def test_angle_between(self):
        self.assertEqual(
            geom.angle_between((1, 0, 0), (0, 1, 0)), angle_90)
        self.assertEqual(geom.angle_between((1, 0, 0), (1, 0, 0)), 0.0)
        self.assertEqual(
            geom.angle_between((1, 0, 0), (-1, 0, 0)), angle_180)
        self.assertAlmostEqual(
            geom.angle_between((1, 0, 1), (0, 0, 1)), angle_45)
        self.assertAlmostEqual(
            geom.angle_between((1, 0, 0), (1, 0, math.tan(angle_60))), angle_60)

    def test_flat_mat(self):
        r = partial(get_rands, 3, lambda r: np.array(r))
        for a, b, c in zip(r(), r(), r()):
            t = Triangle(a, b, c)
            m = geom.get_triangle_flat_mat(t)
            ft = geom.transform_triangle(m, t)
            self.assertAlmostEqual(ft.a[2], ft.b[2], delta=0.0000001)
            self.assertAlmostEqual(ft.a[2], ft.c[2], delta=0.0000001)

    def test_norm(self):
        a = np.array([0, 0, 0])
        b = np.array([1, 0, 0])
        c = np.array([0, 1, 0])
        t = Triangle(a, b, c)
        norm = geom.get_triangle_normal(t)
        self.assertEqual(norm[0], 0)
        self.assertEqual(norm[1], 0)
        self.assertNotEqual(norm[2], 0)

    def test_triangle_inclination(self):
        a, b, c = ((0, 0, 0.00001), (1, 0, 0), (0, 1, 0))
        t = Triangle(np.array(a), np.array(b), np.array(c))

        self.assertAlmostEqual(
            geom.get_triangle_inclination(t), 0, delta=0.001)

        a, b, c = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
        t = Triangle(np.array(a), np.array(b), np.array(c))

        self.assertAlmostEqual(
            geom.get_triangle_inclination(t), 0)

        a, b, c = ((0, 0, 0), (math.sqrt(2), 0, 1), (0, math.sqrt(2), 1))
        t = Triangle(np.array(a), np.array(b), np.array(c))

        self.assertAlmostEqual(
            geom.get_triangle_inclination(t), 45)

        a, b, c = ((0, 0, 0), (0, 0, 1), (0, 1, 0))
        t = Triangle(np.array(a), np.array(b), np.array(c))

        self.assertAlmostEqual(
            geom.get_triangle_inclination(t), 90)

        a, b, c = ((0, 0, 0), (1, 0, math.tan(angle_60)), (1, 1, math.tan(angle_60)))
        t = Triangle(np.array(a), np.array(b), np.array(c))

        self.assertAlmostEqual(
            geom.get_triangle_inclination(t), 60)


if __name__ == '__main__':
    unittest.main()
