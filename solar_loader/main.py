import click
import attr

import django
django.setup()

from .celery import compute_for_all, compute_radiation_for_parcel
from .store import Data
from .tmy import TMY
from .results import make_radiation_file, make_radiation_table, make_results, m_profile, m_incidence, m_profile_day, m_profile_pvlib, compare_sunpos
from django.conf import settings

data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)



@attr.s
class ContextObj:
    config = attr.ib(default=None)


@click.group()
def cli():
    pass


# @cli.command()
# @click.argument('capakey', type=str, required=True)
# @click.argument('sample_rate', type=int, default=30)
# def compute(capakey, sample_rate):
#     click.secho(
#         'Starting with a sample interval of {} days'.format(sample_rate))
#     if 'SOLAR2' in os.environ.keys():
#         get_results_2(data_store, tmy, sample_rate, capakey)
#     else:
#         get_results(data_store, tmy, sample_rate, capakey)

# @cli.command()
# def make_cache():
#     mk_cache()


@cli.command()
@click.argument('sample_rate', type=int, default=30)
@click.argument('limit', type=int, default=10)
@click.argument('offset', type=int, default=0)
def rbc(sample_rate, limit, offset):
    make_results(data_store, tmy, sample_rate, limit, offset)


@cli.command()
@click.argument('filename', type=str, required=True)
@click.argument('sample_rate', type=int, default=30)
def profile(filename, sample_rate):
    m_profile(data_store, tmy, sample_rate, filename)


@cli.command()
@click.argument('filename', type=str, required=True)
@click.argument('sample_rate', type=int, default=30)
def pvlib(filename, sample_rate):
    m_profile_pvlib(data_store, tmy, sample_rate, filename)


@cli.command()
@click.argument('filename', type=str, required=True)
def incidence(filename):
    m_incidence(data_store, tmy, filename)


@cli.command()
@click.argument('filename', type=str, required=True)
def day(filename):
    m_profile_day(data_store, tmy, filename)


@cli.command()
def sunpos():
    compare_sunpos(tmy)


@cli.command()
def radiations_table():
    make_radiation_table(data_store, tmy)


@cli.command()
@click.argument('filename', type=str, required=True)
@click.argument('year', type=int, required=True)
def radiations_file(filename, year):
    make_radiation_file(data_store, tmy, filename, year)


@cli.command()
@click.argument('capakey', type=str, required=True)
def rad(capakey):
    compute_radiation_for_parcel(capakey)


@cli.command()
def all_rad():
    compute_for_all()


def main():
    cli()


if __name__ == '__main__':
    main()
