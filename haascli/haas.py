import click

import haascli


@click.group()
@click.pass_context
def cli(ctx, **kwargs):
    """This is a command line tool for HPCC-as-a-Service (HaaS)
    """
    ctx.obj = kwargs


cli.add_command(haascli.config.cli, name='config')
cli.add_command(haascli.stack.cli, name='stack')
cli.add_command(haascli.cluster.cli, name='cluster')
cli.add_command(haascli.data.cli, name='data')
