import unittest
from solar_loader.radiation import compute_gk  # not tested: roof_rdiso airmass
from data_test_radiation import res_to_check


class TestRadiation(unittest.TestCase):

    def test_roof_rdiso(self):
        pass

    def test_airmass(self):
        pass

    def _test_compute_gk(self, month_step, azimuth_step, inclination_step):
        # month_step >= 1 & month_step < 12
        # azimuth_step a multiple of 90
        # inclination_step a multiple of 5
        alb = 0.2
        i = 5341
        gh = 784
        dh = 174
        sza = 35.6
        saa = -7.3
        alt = 28
        visibility = 1
        for month in range(1, 13, month_step):
            for azimuth in range(0, 360, azimuth_step):
                for inclination in range(0, 91, inclination_step):
                    result = compute_gk(
                        gh, dh, sza, saa, alb, azimuth, inclination, alt,
                        visibility, month, i)

                    if (month, azimuth, inclination) in res_to_check:
                        gk_result = result[0]
                        bk_result = result[1]

                        self.assertAlmostEqual(
                            res_to_check[month, azimuth, inclination][0],
                            gk_result)
                        self.assertAlmostEqual(
                            res_to_check[month, azimuth, inclination][1],
                            bk_result)
                    else:
                        print('UNIT TEST PASSED')

    def test_compute_gk(self):
        self._test_compute_gk(1, 90, 5)


if __name__ == '__main__':
    unittest.main()
