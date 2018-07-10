import unittest
from solar_loader.geom import angle_between


class TestGeom(unittest.TestCase):

    def test_angle_between(self):
        self.assertEqual(
            angle_between((1, 0, 0), (0, 1, 0)), 1.5707963267948966)
        self.assertEqual(
            angle_between((1, 0, 0), (1, 0, 0)), 0.0)
        self.assertEqual(
            angle_between((1, 0, 0), (-1, 0, 0)), 3.141592653589793)


if __name__ == '__main__':
    unittest.main()
