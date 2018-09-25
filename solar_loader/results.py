from functools import partial
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy as np
from time import perf_counter
import math
import csv
from datetime import datetime, timedelta
from pytz import timezone, utc
from pyproj import Proj, transform
from pvlib.irradiance import total_irrad
from pvlib.location import Location
import itertools as it

from .time import hours_for_year
from .lingua import rows_with_geom
from .radiation import compute_gk, incidence
from .sunpos import get_sun_position
from .tmy import make_key
from .rdiso import get_rdiso5

brussels_zone = timezone('Europe/Brussels')
l72 = Proj(init='EPSG:31370')
wgs = Proj(init='EPSG:4326')

def mk_key(t, tilt, azimut):
    return '{:02}{:02}{:02}{:02}{:02}'.format( t.month,t.day,t.hour, tilt,azimut)


def make_radiation_table(db, tmy):
    """
    Make the distribution of radiations over a full range of tilted planes
    throughout the year available as a table.
    """

    db.exec('create_radiations')

    skip_az = 0
    sample_interval = 1
    all_pairs = it.product(range(0, 90, 5), range(skip_az, 360 - skip_az, 5))

    for tilt, azimuth in all_pairs:
        res_row = 0
        res_roof_rdiso_rows = list(
            db.rows(
                'select_res_roof_rdiso',
                {},
                (azimuth, tilt),
            ))

        rdiso_flat = float(res_roof_rdiso_rows[0][0])
        rdiso = float(res_roof_rdiso_rows[0][1])

        for tim in hours_for_year(2018):
            gh = tmy.get_float('G_Gh', tim)
            dh = tmy.get_float('G_Dh', tim)
            hs = tmy.get_float('hs', tim)
            Az = tmy.get_float('Az', tim)
            month = tim.month
            tmy_index = tmy.get_index(tim)

            radiation_global, _ = compute_gk(
                gh,
                dh,
                90.0 - hs,
                Az,
                0.2,
                azimuth,
                tilt,
                28,  # Meteonorm 7 Output Preview for Bruxelles centre
                1,
                month,
                tmy_index,
                rdiso_flat,
                rdiso)

            res_row += radiation_global

        # insert the resulting irradiance
        yearly_rad = res_row * float(sample_interval)
        db.exec('insert_radiation', (float(tilt), float(azimuth), yearly_rad))


def open_multi(fps, m):
    return list(map(lambda fp: open(fp, m), fps))


def make_radiation_file(db, tmy, dest_path, year):
    """
    Make the distribution of radiations over a full range of tilted planes
    throughout the year available as a csv file.
    """

    skip_az = 10

    header = ['time']
    for tilt, azimuth in it.product(
            range(0, 90, 5), range(skip_az, 360 - skip_az, 5)):
        header.append('{}*{}'.format(tilt, azimuth))

    fps = [
        '{}-{}-gk.csv'.format(dest_path, year),
        '{}-{}-bk.csv'.format(dest_path, year),
    ]

    dest_file_gk, dest_file_bk = open_multi(fps, 'w')
    writer_gk = csv.writer(dest_file_gk)
    writer_bk = csv.writer(dest_file_bk)
    writer_gk.writerow(header)
    writer_bk.writerow(header)

    for i, tim in enumerate(hours_for_year(year)):
        print('{}\t{}'.format(i, tim))
        res_row_gk = [tim]
        res_row_bk = [tim]
        rdiso_flat, rdiso = get_rdiso5(azimuth, tilt)

        all_pairs = it.product(
            range(0, 90, 5), range(skip_az, 360 - skip_az, 5))
        for i, (tilt, azimuth) in enumerate(all_pairs):
            gh = tmy.get_float('G_Gh', tim)
            dh = tmy.get_float('G_Dh', tim)
            hs = tmy.get_float('hs', tim)
            Az = tmy.get_float('Az', tim)
            month = tim.month
            tmy_index = tmy.get_index(tim)

            radiation_global, radiation_direct = compute_gk(
                gh,
                dh,
                90.0 - hs,
                Az,
                0.2,
                azimuth,
                tilt,
                28,  # Meteonorm 7 Output Preview for Bruxelles centre
                1,
                month,
                tmy_index,
                rdiso_flat,
                rdiso)

            res_row_gk.append(radiation_global)
            res_row_bk.append(radiation_direct)

        writer_gk.writerow(res_row_gk)
        writer_bk.writerow(res_row_bk)
        # insert the resulting irradiance
        # yearly_rad = res_row * float(sample_interval)
        # db.exec('insert_radiation', (float(tilt), float(azimuth), yearly_rad))


def compute_parcel(db, tmy, sample_rate, ground_row):
    capakey = ground_row[0]
    for roof_row in rows_with_geom(db, 'select_roof_within', (capakey, ), 1):
        # start_roof = perf_counter()
        roof_id = roof_row[0]
        roof_geom = roof_row[1]
        roof_area = roof_row[2]
        gis_triangles = list(get_triangles(db, roof_geom))
        print('roof: {}'.format(roof_id))

        azimuth = np.sum(
            list(map(lambda t: t.get_azimuth() * t.area,
                     gis_triangles))) / roof_area
        tilt = np.sum(
            list(map(lambda t: t.get_inclination() * t.area,
                     gis_triangles))) / roof_area
        radiations = []

        with ProcessPoolExecutor() as executor:
            fn = partial(compute_for_triangles, db, tmy, sample_rate,
                         gis_triangles, True)
            days = generate_sample_days(sample_rate)
            for daily_radiation in executor.map(fn, days):
                radiations.append(daily_radiation * float(sample_rate))

        db.exec('insert_result', (
            capakey,
            roof_id,
            roof_area,
            tilt,
            azimuth,
            np.sum(radiations),
        ))


def make_results(db, tmy, sample_rate, limit, offset):

    start = perf_counter()
    # roof_times = []
    grounds = list(db.rows('select_all_ground', {}, (limit, offset)))
    fn = partial(compute_parcel, db, tmy, sample_rate)
    with ThreadPoolExecutor() as executor:
        executor.map(fn, grounds)

    # for ground_row in db.rows('select_all_ground', {}, (
    #         limit,
    #         offset,
    # )):
    #     capakey = ground_row[0]
    #     print('capakey: {}'.format(capakey))

    #     for roof_row in rows_with_geom(db, 'select_roof_within', (capakey, ),
    #                                    1):
    #         start_roof = perf_counter()
    #         roof_id = roof_row[0]
    #         roof_geom = roof_row[1]
    #         roof_area = roof_row[2]
    #         gis_triangles = list(get_triangles(db, roof_geom))
    #         print('roof: {}'.format(roof_id))

    #         azimuth = np.sum(
    #             list(map(lambda t: t.get_azimuth() * t.area,
    #                      gis_triangles))) / roof_area
    #         tilt = np.sum(
    #             list(
    #                 map(lambda t: t.get_inclination() * t.area,
    #                     gis_triangles))) / roof_area
    #         radiations = []

    #         with ProcessPoolExecutor() as executor:
    #             fn = partial(compute_for_triangles, db, tmy, sample_rate,
    #                          gis_triangles, True)
    #             days = generate_sample_days(sample_rate)
    #             for daily_radiation in executor.map(fn, days):
    #                 radiations.append(daily_radiation * float(sample_rate))

    #         db.exec('insert_result', (
    #             capakey,
    #             roof_id,
    #             roof_area,
    #             tilt,
    #             azimuth,
    #             np.sum(radiations),
    #         ))

    #         roof_times.append(perf_counter() - start_roof)

    print('<{}>'.format(perf_counter() - start))


BXL_CENTER = [149546, 169775, 20]


def m_profile(db, tmy, sample_interval, filename):

    profile = []
    skip_az = 40

    optimal = None

    for tilt in range(0, 90, 5):
        results = []
        for azimuth in range(skip_az, 360 - skip_az, 5):
            res_row = 0
            res_roof_rdiso_rows = list(
                db.rows(
                    'select_res_roof_rdiso',
                    {},
                    (azimuth, tilt),
                ))

            rdiso_flat = float(res_roof_rdiso_rows[0][0])
            rdiso = float(res_roof_rdiso_rows[0][1])

            for tim in generate_sample_times(sample_interval):
                sunpos = get_sun_position(BXL_CENTER, tim)
                if sunpos.is_daylight is False:
                    continue

                # gh = tmy.get_float_average('Global Horizontal Radiation', tim,
                #                            sample_interval)
                # dh = tmy.get_float_average('Diffuse Horizontal Radiation', tim,
                #                            sample_interval)

                gh = tmy.get_float_average('G_Gh', tim, sample_interval)
                dh = tmy.get_float_average('G_Dh', tim, sample_interval)
                hs = tmy.get_float('hs', tim)
                Az = tmy.get_float('Az', tim)
                month = tim.month
                tmy_index = tmy.get_index(tim)

                radiation_global, radiation_direct = compute_gk(
                    gh,
                    dh,
                    90.0 - hs,
                    Az,
                    #sunpos.sza, sunpos.saa,
                    0.2,
                    azimuth,
                    tilt,
                    BXL_CENTER[2],
                    1,
                    month,
                    tmy_index,
                    rdiso_flat,
                    rdiso)

                # radiation_global, radiation_direct = compute_gk_mt(
                #     gh, dh, sunpos.sza, sunpos.saa, 0.2, azimuth, tilt,
                #     BXL_CENTER[2], 1, month, tmy_index)
                res_row += radiation_direct

            yearly_rad = res_row * float(sample_interval)

            if optimal is None:
                optimal = (yearly_rad, tilt, azimuth)
            elif yearly_rad > optimal[0]:
                optimal = (yearly_rad, tilt, azimuth)

            results.append(yearly_rad)
            print('Radiation({}, {}) => {} '.format(
                tilt, azimuth, math.floor(yearly_rad / 1000)))
        profile.append(results)

    print('Optimal({}) => Tilt({}), Azimuth({})'.format(*optimal))

    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        # writer.writerow(map(lambda v: str(v), [t for t in range(0, 360, 5)]))
        for row in profile:
            writer.writerow(map(lambda v: math.floor(v), row))


def m_profile_pvlib(db, tmy, sample_interval, filename):

    profile = []
    skip_az = 40
    lon, lat = transform(l72, wgs, BXL_CENTER[0], BXL_CENTER[1])
    loc = Location(lat, lon, brussels_zone, BXL_CENTER[2])

    optimal = None

    for tilt in range(15, 60, 5):
        results = []
        for azimuth in range(skip_az, 360 - skip_az, 5):

            times = list(generate_sample_times(sample_interval))
            # dni = np.array([
            #     tmy.get_float_average('Direct normal Radiation [Wh/m^2]', tim,
            #                           sample_interval) for tim in times
            # ])
            # ghi = np.array([
            #     tmy.get_float_average('Global Horizontal Radiation', tim,
            #                           sample_interval) for tim in times
            # ])
            # dhi = np.array([
            #     tmy.get_float_average('Diffuse Horizontal Radiation', tim,
            #                           sample_interval) for tim in times
            # ])
            # dni_extra = np.array([
            #     tmy.get_float_average(
            #         'Extraterrestrial Direct Normal Radiation [Wh/m^2]', tim,
            #         sample_interval) for tim in times
            # ])
            dni = np.array([
                tmy.get_float('Direct normal Radiation [Wh/m^2]', tim)
                for tim in times
            ])
            ghi = np.array([
                tmy.get_float('Global Horizontal Radiation', tim)
                for tim in times
            ])
            dhi = np.array([
                tmy.get_float('Diffuse Horizontal Radiation', tim)
                for tim in times
            ])
            dni_extra = np.array([
                tmy.get_float(
                    'Extraterrestrial Direct Normal Radiation [Wh/m^2]', tim)
                for tim in times
            ])
            sunpos = loc.get_solarposition(times)

            airmass = loc.get_airmass(times)

            rad = total_irrad(
                float(tilt),
                float(azimuth),
                sunpos.apparent_zenith,
                sunpos.azimuth,
                dni,
                ghi,
                dhi,
                dni_extra=dni_extra,
                airmass=airmass['airmass_absolute'],
                albedo=0.2,
                model='perez')
            # res_row += rad['poa_global'][0]

            yearly_rad = rad['poa_global'].sum()

            if optimal is None:
                optimal = (yearly_rad, tilt, azimuth)
            elif yearly_rad > optimal[0]:
                optimal = (yearly_rad, tilt, azimuth)

            results.append(yearly_rad)

            print('Radiation({}, {}) => {} '.format(
                tilt, azimuth, math.floor(yearly_rad / 1000.0)))

        profile.append(results)

    print('Optimal({}) => Tilt({}), Azimuth({})'.format(*optimal))

    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        # writer.writerow(map(lambda v: str(v), [t for t in range(0, 360, 5)]))
        for row in profile:
            writer.writerow(map(lambda v: math.floor(v), row))


def m_incidence(db, tmy, filename):
    sample_rate = 30
    profile = []
    skip_az = 40
    optimal = None

    for tilt in range(35, 50, 5):
        results = []
        for azimuth in range(skip_az, 360 - skip_az, 5):
            res_row = 0.0

            for tim in generate_sample_times(sample_rate):
                gh = tmy.get_float('Global Horizontal Radiation', tim)
                dh = tmy.get_float('Diffuse Horizontal Radiation', tim)
                sunpos = get_sun_position(BXL_CENTER, tim)

                inc, rad = incidence(gh, dh, sunpos.sza, sunpos.saa, azimuth,
                                     tilt)
                res_row += inc

            yearly_rad = res_row * float(sample_rate)
            results.append(yearly_rad)

            print('({}, {}) => {} '.format(tilt, azimuth, yearly_rad))

            if optimal is None:
                optimal = (yearly_rad, tilt, azimuth)
            elif yearly_rad > optimal[0]:
                optimal = (yearly_rad, tilt, azimuth)

        profile.append(results)

    print('Optimal({}) => Tilt({}), Azimuth({})'.format(*optimal))

    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for row in profile:
            writer.writerow(row)


def m_profile_day(db, tmy, filename):

    profile = []
    sample_interval = 30
    tilt = 35
    azimuth = 180
    lon, lat = transform(l72, wgs, BXL_CENTER[0], BXL_CENTER[1])
    loc = Location(lat, lon, brussels_zone, BXL_CENTER[2])

    # res_roof_rdiso_rows = list(
    #     db.rows(
    #         'select_res_roof_rdiso',
    #         {},
    #         (azimuth, tilt),
    #     ))

    # rdiso_flat = float(res_roof_rdiso_rows[0][0])
    # rdiso = float(res_roof_rdiso_rows[0][1])

    # profile.append(('Time', 'radiation_global', 'radiation_direct', 'gh', 'dh',
    #                 'sza', 'saa'))

    now = datetime.now(brussels_zone)
    start = datetime(now.year, 8, 15, 0, 0, 0, 0, brussels_zone)
    d = timedelta(hours=1)
    # for tim in [start + (d * i) for i in range(24)]:

    profile.append(
        ('tim.strftime', 'make_key', 'sunpos.sza', 'sunpos.saa + 180', 'aoi0',
         'inc0', 'rad0', 'aoi1', 'inc1', 'rad1', 'aoi2', 'inc2', 'rad2'))
    for tim in generate_sample_times(sample_interval):

        sunpos = get_sun_position(BXL_CENTER, tim)
        pv_sunpos = loc.get_solarposition(tim)
        if sunpos.is_daylight is False:
            continue

        # gh = tmy.get_float_average('Global Horizontal Radiation', tim,
        #                            sample_interval)
        # dh = tmy.get_float_average('Diffuse Horizontal Radiation', tim,
        #                            sample_interval)

        gh = tmy.get_float_average('G_Gh', tim, sample_interval)
        dh = tmy.get_float_average('G_Dh', tim, sample_interval)
        hs = tmy.get_float('hs', tim)
        Az = tmy.get_float('Az', tim)

        # print('SP => {}  {}  {}'.format(Az, sunpos.saa,
        #                                 pv_sunpos.azimuth - 180))

        aoi0, inc0, rad0 = incidence(gh, dh, 90.0 - hs, Az, azimuth, tilt)
        aoi1, inc1, rad1 = incidence(gh, dh, 90.0 - hs, Az, azimuth + 10, tilt)
        aoi2, inc2, rad2 = incidence(gh, dh, 90.0 - hs, Az, azimuth + 20, tilt)

        # aoi0, inc0, rad0 = incidence(gh, dh, sunpos.sza, sunpos.saa, azimuth,
        #                              tilt)
        # aoi1, inc1, rad1 = incidence(gh, dh, sunpos.sza, sunpos.saa,
        #                              azimuth + 10, tilt)
        # aoi2, inc2, rad2 = incidence(gh, dh, sunpos.sza, sunpos.saa,
        #                              azimuth + 20, tilt)

        print(
            '{}::{}::[{:.1f},{:.1f}]\t({:.2f}\t{:.2f}\t{:.2f})\t({:.2f}\t{:.2f}\t{:.2f})\t({:.2f}\t{:.2f}\t{:.2f})'.
            format(
                tim.strftime('%B'), make_key(tim), sunpos.sza,
                sunpos.saa + 180, aoi0, inc0, rad0, aoi1, inc1, rad1, aoi2,
                inc2, rad2))
        profile.append((tim.strftime('%B'), make_key(tim),
                        sunpos.sza, sunpos.saa + 180, round(aoi0), round(inc0),
                        round(rad0), round(aoi1), round(inc1), round(rad1),
                        round(aoi2), round(inc2), round(rad2)))

        # radiation_global, radiation_direct = compute_gk(
        #     gh, dh, sunpos.sza, sunpos.saa, 0.2, azimuth, tilt, BXL_CENTER[2],
        #     1, month, tmy_index, rdiso_flat, rdiso)

        # profile.append((tim.isoformat(), radiation_global, radiation_direct,
        #                 gh, dh, sunpos.sza, sunpos.saa))

        # print('Radiation({}, {}) => {} '.format(
        #     tilt, azimuth, math.floor(yearly_rad / 1000)))

    # return

    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for row in profile:
            writer.writerow(row)


def compare_sunpos(tmy):
    n_h = 24 * 7
    lon, lat = transform(l72, wgs, BXL_CENTER[0], BXL_CENTER[1])
    loc = Location(lat, lon, brussels_zone, BXL_CENTER[2])
    now = datetime.now(brussels_zone)
    now_utc = datetime.now(utc)

    start = datetime(now.year, now.month, now.day, 0, 0, 0, 0, brussels_zone)
    start_utc = datetime(now_utc.year, now_utc.month, now_utc.day, 0, 0, 0, 0,
                         utc)
    d = timedelta(hours=1)

    sp_tmy = [(tmy.get_float('hs', tim), tmy.get_float('Az', tim) + 180.0)
              for tim in time_range(start, d, n_h)]

    psp = partial(get_sun_position, BXL_CENTER)
    sp_sunpos = [(sp.elevation, sp.azimuth)
                 for sp in map(psp, time_range(start, d, n_h, utc))]

    pvlib_result = loc.get_solarposition(time_range(start, d, n_h, utc))
    sp_pvlib = list(
        zip(pvlib_result.elevation.values, pvlib_result.azimuth.values))

    print('                                tmy     \tsunpos    \tpvlib')
    for i, t in enumerate(time_range(start, d, n_h)):
        print(
            '{}:\t({:.2f}, {:.2f})\t({:.2f}, {:.2f})\t({:.2f}, {:.2f})'.format(
                t,
                sp_tmy[i][0],
                sp_tmy[i][1],
                sp_sunpos[i][0],
                sp_sunpos[i][1],
                sp_pvlib[i][0],
                sp_pvlib[i][1],
            ))
