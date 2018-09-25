import click
import attr

import django
django.setup()

from .final import compute_for_all, display_diff
from .store import Data
from .tmy import TMY
from .results import (make_radiation_file, make_radiation_table, make_results,
                      m_profile, m_profile_day, m_profile_pvlib,
                      compare_sunpos)
from .time import start_counter, summarize_times
from .compute import get_results_roof
from django.conf import settings


@attr.s
class ContextObj:
    config = attr.ib(default=None)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--shadows', is_flag=True)
@click.argument('roof_id', type=str, required=True)
@click.argument('sample_rate', type=int, default=30)
def compute(shadows, roof_id, sample_rate):
    data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    tmy = TMY(settings.SOLAR_TMY)
    start_counter()
    r = get_results_roof(data_store, tmy, sample_rate, roof_id, shadows)
    summarize_times()
    props = r['properties']
    i = props['irradiance']
    a = props['area']
    click.secho('irradiance = {} w, area = {} m2'.format(i, a), fg='blue')


@cli.command()
@click.argument('sample_rate', type=int, default=30)
@click.argument('limit', type=int, default=10)
@click.argument('offset', type=int, default=0)
def rbc(sample_rate, limit, offset):
    data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    tmy = TMY(settings.SOLAR_TMY)
    make_results(data_store, tmy, sample_rate, limit, offset)


@cli.command()
@click.argument('filename', type=str, required=True)
@click.argument('sample_rate', type=int, default=30)
def profile(filename, sample_rate):
    data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    tmy = TMY(settings.SOLAR_TMY)
    m_profile(data_store, tmy, sample_rate, filename)


@cli.command()
@click.argument('filename', type=str, required=True)
@click.argument('sample_rate', type=int, default=30)
def pvlib(filename, sample_rate):
    data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    tmy = TMY(settings.SOLAR_TMY)
    m_profile_pvlib(data_store, tmy, sample_rate, filename)


@cli.command()
@click.argument('filename', type=str, required=True)
def day(filename):
    data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    tmy = TMY(settings.SOLAR_TMY)
    m_profile_day(data_store, tmy, filename)


@cli.command()
def sunpos():
    tmy = TMY(settings.SOLAR_TMY)
    compare_sunpos(tmy)


@cli.command()
def radiations_table():
    data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    tmy = TMY(settings.SOLAR_TMY)
    make_radiation_table(data_store, tmy)


@cli.command()
@click.argument('filename', type=str, required=True)
@click.argument('year', type=int, required=True)
def radiations_file(filename, year):
    data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
    tmy = TMY(settings.SOLAR_TMY)
    make_radiation_file(data_store, tmy, filename, year)


# @cli.command()
# @click.argument('capakey', type=str, required=True)
# def rad(capakey):
#     compute_radiation_for_parcel(capakey)


@cli.command()
@click.option('--limit', type=int)
@click.option('--offset', type=int)
def all_rad(limit, offset):
    compute_for_all(limit, offset)


@cli.command()
def diff():
    display_diff()


def main():
    cli()


if __name__ == '__main__':
    main()
