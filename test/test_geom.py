import unittest
import numpy as np
from random import random
from functools import partial
from solar_loader import geom
from solar_loader.records import Triangle
import math

SERIE_COUNT = 12

angle_60 = math.pi / 3
angle_90 = math.pi / 2


def get_rands(n, f):
    for i in range(SERIE_COUNT):
        r = []
        for i in range(n):
            r.append(random() * 1000.0)
        yield f(r)


class TestGeom(unittest.TestCase):
    def test_vec_dist(self):
        """Test together the functions geom.vec2_dist and geom.vec_dist"""
        self.assertEqual(
            geom.vec2_dist((0, 0), (1, 1)),
            geom.vec_dist(np.array((0, 0)), np.array((1, 1))))  # math.sqrt(2)

        self.assertEqual(
            geom.vec2_dist((-1.5, 1), (0.5, 2.5)),
            geom.vec_dist(
                np.array((-1.5, 1)),
                np.array((0.5, 2.5))), math.sqrt(6.25)
            )  # math.sqrt(6.25))

    def test_vec3_add(self):
        # vec3_add is not used -> not tested
        pass

    def test_rotation_matrix(self):
        """Test the function geom.rotation_matrix"""
        for div in [1, 2, 3, 6]:
            angle = math.pi / div
            r = geom.rotation_matrix((0, 0, 1), angle)
            check = np.matrix([
                [math.cos(angle), -math.sin(angle), 0],
                [math.sin(angle), math.cos(angle), 0],
                [0, 0, 1]
            ])
            np.testing.assert_array_almost_equal(r, check)

            r = geom.rotation_matrix((1, 0, 0), angle)
            check = np.matrix([
                [1, 0, 0],
                [0, math.cos(angle), -math.sin(angle)],
                [0, math.sin(angle), math.cos(angle)],

            ])
            np.testing.assert_array_almost_equal(r, check)

            r = geom.rotation_matrix((0, 1, 0), angle)
            check = np.matrix([
                [math.cos(angle), 0, math.sin(angle)],
                [0, 1, 0],
                [-math.sin(angle), 0, math.cos(angle)],
            ])
            np.testing.assert_array_almost_equal(r, check)

    def test_get_centroid(self):
        # get_centroid is not used -> not tested
        pass

    def test_get_triangle_normal(self):
        """Test for the function geom.norm"""
        for a, b, c, res_unit in [
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)],
            [(0, 12, 0), (0, 0, 1), (0, 0, 0), (1, 0, 0)],
            [(0, 0, 0), (11, 0, 0), (0, 0, 1), (0, -1, 0)],
            [(1, 0, 0), (0, 1, 0), (0, 0, 1), (
                math.sqrt(1/3), math.sqrt(1/3), math.sqrt(1/3))],
        ]:
            t = Triangle(np.array(a), np.array(b), np.array(c))
            norm = geom.get_triangle_normal(t)
            norm_unit = geom.unit_vector(norm)
            np.testing.assert_array_almost_equal(norm_unit, res_unit)

    def test_get_triangle_azimut(self):
        """Test for the function geom.get_triangle_azimut"""
        for a, b, c, azim, delta in [
            [(0, 0, 0), (0, 0, 1), (1, 0, 0), 0, None],
            [(0, 0, 0), (0, 0, 1), (0, 1, 0), 90, 0.01],
            [(0, 0, 0), (0, 0, 1), (-1, 0, 0), 180, None],
            [(0, -1, 0), (0, 0, 0), (0, 0, 1), 270, 0.01],
            [(0, 0, 0), (0, -1, 0), (0, 0, 1), 90, 0.01],
            [(0, 0, 0), (0, 0, 1), (0, -1, 0), 270, 0.01],
            [(1, 0, 0), (0, 1, 0), (0, 0, 1), 315, None],
            [(0, 1, 0), (-1, 0, 0), (0, 0, 1), 45, None],
            [(-1, 0, 0), (0, -1, 0), (0, 0, 1), 135, None],
            [(0, -1, 0), (1, 0, 0), (0, 0, 1), 225, None],
        ]:
            t = Triangle(np.array(a), np.array(b), np.array(c))
            self.assertAlmostEqual(
                geom.get_triangle_azimut(t), azim, delta=delta)

    def test_triangle_inclination(self):
        """Test for get_triangle_inclination"""

        # Check if Triangle(a, b, c) has an inclination of delta (delta can
        # be use for specifying the precision)
        for a, b, c, res, delta in [
            [(0, 0, 0.00001), (1, 0, 0), (0, 1, 0), 0, 0.001],
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), 0, None],
            [(0, 0, 0), (math.sqrt(2), 0, 1), (0, math.sqrt(2), 1), 45, None],
            [(0, 0, 0), (0, 0, 1), (0, 1, 0), 90, 0.01],
            [
                (0, 0, 0),
                (1, 0, math.tan(angle_60)),
                (1, 1, math.tan(angle_60)), 60, None
            ],
            [(1, 0, 0), (0, 1, 0), (0, 0, 1 / math.sqrt(2)), 45, None],
            [(0, 1, 0), (-1, 0, 0), (0, 0, 1 / math.sqrt(2)), 45, None],
            [(-1, 0, 0), (0, -1, 0), (0, 0, 1 / math.sqrt(2)), 45, None],
            [(0, -1, 0), (1, 0, 0), (0, 0, 1 / math.sqrt(2)), 45, None],


        ]:
            t = Triangle(np.array(a), np.array(b), np.array(c))
            self.assertAlmostEqual(
                geom.get_triangle_inclination(t), res, delta=delta)

    def test_get_triangle_center(self):
        # TODO
        pass

    def test_transform_triangle(self):
        # TODO
        pass

    def transform_multipolygon(self):
        # TODO
        pass

    def polygon_drop_z(self):
        # TODO
        pass

    def test_triangle_from_shape(self):
        # TODO
        pass

    def test_tesselate(self):
        # TODO
        pass

    def test_flat_mat(self):
        """Test for the function geom.flat_mat"""
        # TODO revoir
        r = partial(get_rands, 3, lambda r: np.array(r))
        for a, b, c in zip(r(), r(), r()):
            t = Triangle(a, b, c)
            m = geom.get_triangle_flat_mat(t)
            ft = geom.transform_triangle(m, t)
            self.assertAlmostEqual(ft.a[2], ft.b[2], delta=0.0000001)
            self.assertAlmostEqual(ft.a[2], ft.c[2], delta=0.0000001)

    def test_get_triangle_flat_mat(self):
        pass

    def test_unit_vector(vector):
        pass

    def test_angle_between(self):
        """Test for the function geom.angle_between"""
        self.assertAlmostEqual(
            geom.angle_between([1, 0, 0], [0, 1, 0]), angle_90, delta=0.01)
        self.assertEqual(geom.angle_between([1, 0, 0], [1, 0, 0]), 0.0)
        self.assertEqual(
            np.rad2deg(geom.angle_between([1, 0, 0], [-1, 0, 0])), 180)
        self.assertAlmostEqual(
            np.rad2deg(geom.angle_between([1, 0, 1], [0, 0, 1])), 315)
        self.assertAlmostEqual(
            np.rad2deg(
                geom.angle_between([1, 0, 0], [1, 0, math.tan(angle_60)])),
            300)
        self.assertAlmostEqual(
            geom.angle_between([-1, 0, 0], [0, 1, 0]),
            math.pi * 3 / 2, delta=0.01)
        self.assertAlmostEqual(
            np.rad2deg(geom.angle_between([0, 1, 0], [-1, 0, 0])), 90)
        self.assertAlmostEqual(
            np.rad2deg(geom.angle_between([0, -1, 0], [0, 0, 1])), 90)


if __name__ == '__main__':
    unittest.main()
