import click
import attr
import json

from .pg import DB
from .tmy import TMY
from .compute import get_results


@attr.s
class ContextObj:
    config = attr.ib(default=None)


@click.group()
@click.pass_context
@click.option('--config', type=click.File(), required=True)
def cli(ctx, config):
    ctx.obj.config = json.load(config)


@cli.command()
@click.argument('ground_id', type=str, required=True)
@click.argument('sample', type=int, default=30)
@click.pass_context
def ground(ctx, ground_id, sample):
    config = ctx.obj.config
    click.secho('Starting with a sample interval of {} days'.format(sample))
    get_results(
        DB(config['dsn'], config['tables']), TMY(config['tmy']), sample,
        ground_id)


def main():
    cli(obj=ContextObj())


if __name__ == '__main__':
    main()