import unittest
from solar_loader import sunpos
import numpy as np
from pysolar import solar
from datetime import datetime, timezone

class TestSunPos(unittest.TestCase):
    def test_inverse_azimut(self):
        """ Test the inverse of the azimut"""
        verif = [
            # (azimut (degree), x, y)
            (0, 0, 1),
            (90, 1, 0),
            (180, 0, -1),
            (270, -1, 0),
        ]

        for v in verif:
            azimut = v[0]
            x_to_check = v[1]
            y_to_check = v[2]
            res = sunpos._get_coords_from_angles((0, 0, 0), 0, np.deg2rad(azimut), 1)
            self.assertAlmostEqual(res[0], x_to_check)
            self.assertAlmostEqual(res[1], y_to_check)

    def test_get_sun_position(self):
        self.skipTest('ToDo')

    def test_azimuth_modulo_360(self):
        self.assertEqual(-1.5 % 360, 358.5)
        self.assertEqual(-1 % 360, 359)
        self.assertEqual(380 % 360, 20)
        self.assertAlmostEqual(366.7 % 360, 6.7)
        self.assertEqual(90 % 360, 90)
        self.assertEqual(360 % 360, 0)
        self.assertEqual(0 % 360, 0)

    def test_pysolar_get_azimut(self):
        bxl_lon = 4.3528
        bxl_lat = 50.8466

        hours = [8, 10, 12, 14, 16, 18]

        for h in hours:
            # utc_date = datetime(2017, 6, 21, hour=h, tzinfo=utc)
            utc_date = datetime(2017, 9, 21, hour=h, tzinfo=timezone.utc)
            # is heigth in meters ?
            azim = solar.get_azimuth(bxl_lat, bxl_lon, utc_date, 13)
            print('{} -> azimuth : {}'.format(utc_date, azim))

if __name__ == '__main__':
    unittest.main()
