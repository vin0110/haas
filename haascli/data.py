import click


@click.group()
@click.pass_context
def cli(ctx, **kwargs):
    """Data related operations
    """
    ctx.obj = kwargs


@cli.command()
@click.pass_context
def save(ctx):
    pass


@cli.command()
@click.pass_context
def restore(ctx):
    pass


@cli.command()
@click.pass_context
def resize(ctx):
    pass
