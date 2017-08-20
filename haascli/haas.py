import os
import logging

import click

import haascli
from haascli import config as haascli_config
from haascli import cluster as haascli_cluster
from haascli import stack as haascli_stack
from haascli import data as haascli_data


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--debug/--no-debug', default=False)
@click.option('--exec/--no-exec', default=True)
# @click.option('--provider', type=click.Choice(['aws', 'azure']),
#               default='aws')
@click.option('--config_dir',
              type=click.Path(exists=True, resolve_path=True),
              default=lambda: os.path.join(os.path.expanduser('~'), '.haas'),
              help="The haas configuration directory")
@click.option('--log/--no-log', default=False)
@click.option('-L', '--log-file',
              default=haascli.DEFAULT_LOG,
              help='set log file; default "{}"; "-" for stdout'
              .format(haascli.DEFAULT_LOG))
@click.option('-r', '--region', help='AWS region name')
@click.option('-k', '--key', help='AWS key')
@click.option('-s', '--secret', help='AWS secret key')
@click.pass_context
def cli(ctx, **kwargs):
    """This is a command line tool for HPCC-as-a-Service (HaaS)
    """
    ctx.obj = kwargs

    haascli.setup_logging(
        level=logging.DEBUG if kwargs['debug'] else logging.INFO,
        file=kwargs['log_file'] if kwargs['log'] else None)


cli.add_command(haascli_config.cli, name='config')
cli.add_command(haascli_stack.cli, name='stack')
cli.add_command(haascli_cluster.cli, name='cluster')
cli.add_command(haascli_data.cli, name='data')
