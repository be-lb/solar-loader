import os
import click
import attr
import json

import django
django.setup()

from .store import Data
from .tmy import TMY
from .compute import get_results, get_results_2
from .radiation_cache import mk_cache
from .results import make_results, m_profile, m_incidence, m_profile_day, m_profile_pvlib, compare_sunpos
from django.conf import settings

data_store = Data(settings.SOLAR_CONNECTION, settings.SOLAR_TABLES)
tmy = TMY(settings.SOLAR_TMY)


@attr.s
class ContextObj:
    config = attr.ib(default=None)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('capakey', type=str, required=True)
@click.argument('sample_rate', type=int, default=30)
def compute(capakey, sample_rate):
    click.secho(
        'Starting with a sample interval of {} days'.format(sample_rate))
    if 'SOLAR2' in os.environ.keys():
        get_results_2(data_store, tmy, sample_rate, capakey)
    else:
        get_results(data_store, tmy, sample_rate, capakey)


@cli.command()
def make_cache():
    mk_cache()


@cli.command()
def rbc():
    make_results(data_store, tmy, 30)


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


def main():
    cli()


if __name__ == '__main__':
    main()
