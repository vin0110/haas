import os

import click

import haascli


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--debug/--no-debug', default=False)
@click.option('--exec/--no-exec', default=True)
# @click.option('--provider', type=click.Choice(['aws', 'azure']),
#               default='aws')
@click.option('--config_dir',
              type=click.Path(exists=True, resolve_path=True),
              default=lambda: os.path.join(os.path.expanduser('~'), '.haas'),
              help="The haas configuration directory")
@click.option('-r', '--region', help='AWS region name')
@click.option('-k', '--key', help='AWS key')
@click.option('-s', '--secret', help='AWS secret key')
@click.pass_context
def cli(ctx, **kwargs):
    """This is a command line tool for HPCC-as-a-Service (HaaS)
    """
    ctx.obj = kwargs
    ctx.cc = kwargs

    if 'config_dir' not in ctx.obj:
        os.mkdirs(ctx.obj['config_dir'])



cli.add_command(haascli.config.cli, name='config')
cli.add_command(haascli.stack.cli, name='stack')
cli.add_command(haascli.cluster.cli, name='cluster')
cli.add_command(haascli.data.cli, name='data')
