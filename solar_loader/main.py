import click
import attr
import json

import django
django.setup()

from .store import Data
from .tmy import TMY
from .compute import get_results
from .radiation_cache import mk_cache
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
    get_results(data_store, tmy, sample_rate, capakey)


@cli.command()
def make_cache():
    mk_cache()


def main():
    cli()


if __name__ == '__main__':
    main()
