# -*- coding: iso-8859-1 -*-
#
"""
This module contains functions to calculate solar radiation on inclined
surface.

Project: Carte solaire bruxelloise
Usage under the GNU Affero General Public License
Authors: Daniel Klauser / Simon Albrecht, Meteotest AG, 3012 Bern, Switzerland
"""

import numpy as np
from math import pi, exp, sin, cos, radians, floor

# constants for compute_gk
epsilons = np.array([1.065, 1.23, 1.5, 1.95, 2.8, 4.5, 6.2, 10])
f1 = np.array([[-0.008, 0.13, 0.33, 0.568, 0.873, 1.132, 1.06, 0.678], [
    0.588, 0.683, 0.487, 0.187, -0.392, -1.237, -1.6, -0.327
], [-0.062, -0.151, -0.221, -0.295, -0.362, -0.412, -0.359, -0.25]])
f2 = np.array([[-0.06, -0.019, 0.055, 0.109, 0.226, 0.288, 0.264, 0.156],
               [0.072, 0.066, -0.064, -0.152, -0.462, -0.823, -1.127, -1.377],
               [-0.022, -0.029, -0.026, -0.014, 0.001, 0.056, 0.131, 0.251]])
days_in_months_before = np.array(
    [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334])

# albedo for Brussels:
alb = 0.2


def compute_gk(gh,
               dh,
               sza,
               saa,
               alb,
               azimuth,
               inclination,
               alt,
               visibility,
               month,
               i,
               rdiso_flat=None,
               rdiso=None):
    """
    compute irradiation on inclined surface.

    Returns global (=gk) and direct (=bk) irradiance (W/m2) on inclined
    surface as a float.

    Includes cicumsolar and horizon band anisotropic distribution according
    to PEREZ model.

    Source : Solar Energy Vol.44, No 5, pp. 271-289, 1990.

    keyword arguments:

    gh              global horizontal radiation in W/m2 (input from TMY)
    dh              diffuse horizontal radiation in W/m2 (input from TMY)
    sza             solar zenit angle (0 = zenit, 90 = horizon) (input from
                    TMY)
    saa             solar azimuth angle (degrees between -180 to +180 as input
                    from TMY, converted in code to 0 to 360)
    alb             albedo (between 0 and 1) --> constant value for Brussels
    azimuth         azimuth of roof plane (degrees between 0 and 360,
                    0/360=north, 90�=east,180�=south,270�=west)
    inclination     inclination of roof plane (degrees between 0 (flat) and
                    90 (fascade))
    alt             altitude of roof plane above sea level
    visibility      visibility (0 = shadowed, 1 = sunny, float value between 0
                    and 1 = partially shadowed)
    month           month (from 1 to 12)
    i            	index of TMY for hour of year: 0-8760
    rdiso_flat      (optionnal)
    rdiso           (optionnal)


    All angles are assumed to be given in degrees, i.e. [�], and converted to
    radians within this method.

    The calculation follows the mn-theory handbook section 6.7.2
    """

    # calculate isometric rd factors for flat plane (rdiso_flat) and inclined
    # plane (rdiso):

    if rdiso_flat is None or rdiso is None:
        roofrdiso = roof_rdiso(azimuth, inclination, visibility)
        rdiso_flat = roofrdiso[0]
        rdiso = roofrdiso[1]

    # day of year:
    dayofyear = 1 + days_in_months_before[month - 1] + floor(i / 24.0)

    # calculate direct horizontal irradiance bh
    bh = gh - dh

    if gh <= 0:
        return 0.0, 0.0
    if bh >= 0.95 * gh:
        bh = 0.95 * gh
    if alb > 1:
        alb = 1

    # convert azimuth from TMY (-180 to 180) to 0-360:
    saa = saa + 180

    # make sure that sun is above horizon
    sza = min(89, sza)
    # convert angels to [rad]
    azimuth = radians(azimuth)
    inclination = radians(inclination)
    saa = radians(saa)
    sza = radians(sza)

    # calculate the cosine of theta_gen, the incident angle of the sun on the
    # inclined plane, i.e. the angle between the direction of the sun then the
    # normal vector of the plane
    cos_theta_gen = max(0, (sin(sza) * sin(inclination) * cos(saa - azimuth) +
                            cos(sza) * cos(inclination)))

    # calculate PEREZ MODEL parameter delta
    hs = (pi / 2.0) - sza
    am = airmass(hs, alt)
    # extraterrestrial radiation: mn-theory section 6.4
    i0 = 1367 * (1 + 0.03344 * cos(2 * pi * dayofyear / 365.25 - 0.048869))
    delta = dh * am / i0

    # calculate PEREZ MODEL parameter epsilon
    epsilon = (1.0 + bh / (dh * sin(hs)) + 1.041 * (sza**3)) / (1.0 + 1.041 *
                                                                (sza**3))

    # CIRCUMSOLAR AND HORIZON BRIGHTENING COEFFICIENTS F1 and F2
    eps = 0
    while eps < 7 and epsilon >= epsilons[eps]:
        eps += 1
    f1_coeff = f1[0, eps] + f1[1, eps] * delta + f1[2, eps] * sza
    f2_coeff = f2[0, eps] + f2[1, eps] * delta + f2[2, eps] * sza

    # calculate gh_hor and dh_hor. a/b = 1 is assumed for consistency.
    gh_hor = ((visibility * (bh + dh * f1_coeff) + dh *
               (1 - f1_coeff) * rdiso_flat) / (1 - (1 - rdiso_flat) * alb))

    # direct irradiance on inclined plane
    # bk = visibility * bh * rate  # cos_theta_gen / cos(sza)
    bk = visibility * bh * cos_theta_gen / cos(sza)
    # diffuse irradiance: circumsolar part
    dif_cs = visibility * dh * f1_coeff * cos_theta_gen / max(0.087, cos(sza))
    # diffuse irradiance: reflected part
    dif_ref = gh_hor * alb * (1 - rdiso)
    # diffuse irradiance: isotropic
    dif_iso = dh * (1 - f1_coeff) * rdiso
    # diffuse irradiance: horizontal ribbon
    dif_horrib = dh * f2_coeff * sin(inclination)
    # sum all components of gk
    gk = bk + dif_cs + dif_ref + dif_iso + dif_horrib

    return max(0, gk), max(0, bk)


# constants for computing roof_rdiso
PI_DIV_90_360 = pi / (90 * 360)


def roof_rdiso(azimuth, inclination, visibility):
    """
    calculates the isotropic diffus view factor given azimuth and inclination
    of a the roof plane and a horizon matrix.

    returns rdiso for flat plane and inclined plane
    """

    rdiso = 0
    rdiso_flat = 0

    cos_radians_inclination = cos(radians(inclination))
    sin_radians_inclination = sin(radians(inclination))

    for phi in range(0, 360):
        cos_rad_phi_minus_azimuth = cos(radians(phi - azimuth))
        sin_radians_inclination_x_cos_rad_phi_minus_azimuth = \
            sin_radians_inclination * cos_rad_phi_minus_azimuth
        for theta in range(0, 90):
            # use angle of the center of the sky element
            theta = theta + 0.5
            rdiso += PI_DIV_90_360 * sin(radians(theta)) * visibility *\
                max(
                    sin(radians(theta)) *
                    sin_radians_inclination_x_cos_rad_phi_minus_azimuth +
                    cos(radians(theta)) * cos_radians_inclination,
                    0)
            rdiso_flat += PI_DIV_90_360 * sin(radians(theta)) * visibility *\
                cos(radians(theta))
    return max(0.0, min(1.0, rdiso_flat)), max(0.0, min(1.0, rdiso))


# constants for computingairmass
AIRMASS_HST_4_NEG_HS = 0.061359 * 0.1594
AIRMASS_DIVIDER_4_NEG_HS = (sin(AIRMASS_HST_4_NEG_HS) + 0.50572 *
                            (AIRMASS_HST_4_NEG_HS + 6.07995)**-1.6364)


def airmass(hs, alt):
    """
    compute optical air mass according to mn theory 6.3.7

    """
    alt_corr = exp(-alt / 8435.2)
    if hs < 0:
        airmass = alt_corr / AIRMASS_DIVIDER_4_NEG_HS
    else:
        hst = hs + 0.061359 * (0.1594 + 1.123 * hs + 0.065656 * hs**2) / (
            1 + 28.9344 * hs + 277.3971 * hs**2)
        airmass = alt_corr / (sin(hst) + 0.50572 * (hst + 6.07995)**-1.6364)
    return airmass
