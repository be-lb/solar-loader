from django.conf import settings
from django.db import connections
from .compute import generate_sample_days
from .radiation import roof_rdiso, compute_gk
from .tmy import TMY


def get_azimuth(azimuth_step):
    return range(0, 360, azimuth_step)


def get_inclination(inclination_step):
    return range(0, 91, inclination_step)


def compute_rdiso_cache(cur, azimuth_step, inclination_step):
    # DEFAULT PARAMETERS
    visibility = 1

    # CREATE TABLE
    cur.execute('DROP TABLE IF EXISTS solar.res_roof_rdiso')
    cur.execute("""CREATE TABLE solar.res_roof_rdiso
    (
        azimuth smallint,
        inclination smallint,
        rdiso_flat decimal,
        rdiso decimal,
        CONSTRAINT res_roof_rdiso_pkey PRIMARY KEY (azimuth, inclination)
    )""")

    # INSERT DATA
    for azimuth in get_azimuth(azimuth_step):
        for inclination in get_inclination(inclination_step):
            rdiso_flat, rdiso = roof_rdiso(azimuth, inclination, visibility)
            sql = 'INSERT INTO solar.res_roof_rdiso \
("azimuth", "inclination", "rdiso_flat", "rdiso") \
VALUES ({}, {}, {}, {});'.format(azimuth, inclination, rdiso_flat, rdiso)
            cur.execute(sql)


def compute_radiations_cache(cur, azimuth_step, inclination_step):
    # DEFAULT PARAMETERS
    sample_rate = settings.SOLAR_SAMPLE_RATE
    days = generate_sample_days(sample_rate)
    sza = 88.26762935193963
    saa = -272.0074355339058
    alt = 54.56066666666667
    alb = 2
    tmy = TMY(settings.SOLAR_TMY)

    # CREATE TABLE
    cur.execute('DROP TABLE IF EXISTS solar.radiations')
    cur.execute("""CREATE TABLE solar.radiations
    (
        day timestamp,
        azimuth smallint,
        inclination smallint,
        radiation_global decimal,
        radiation_direct decimal,
        CONSTRAINT raditions_pkey PRIMARY KEY (day, azimuth, inclination)
    )""")

    # INSERT DATA
    for day in days:
        for tim in day:
            gh = tmy.get_float('Global Horizontal Radiation', tim)
            dh = tmy.get_float('Diffuse Horizontal Radiation', tim)
            month = tim.month
            tmy_index = tmy.get_index(tim)

            for azimuth in get_azimuth(azimuth_step):
                for inclination in get_inclination(inclination_step):
                    radiation_global, radiation_direct = compute_gk(
                        gh, dh, sza, saa, alb, azimuth,
                        inclination, alt, 1, month, tmy_index)

                    sql = 'INSERT INTO solar.radiations \
("day", "azimuth", "inclination", "radiation_global", "radiation_direct") \
VALUES ({}, {}, {}, {}, {});'.format(
                        day, azimuth, inclination, radiation_global,
                        radiation_direct)
                    cur.execute(sql)


def mk_cache():
    conn = connections[settings.SOLAR_CONNECTION]
    with conn.cursor() as cur:
        # compute_radiations_cache(cur, 5, 5)
        compute_rdiso_cache(cur, 5, 5)
