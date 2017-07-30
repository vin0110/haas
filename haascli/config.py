import click


@click.group()
@click.pass_context
def cli(ctx, **kwargs):
    """Data related operations
    """
    ctx.obj = kwargs


@cli.command()
@click.pass_context
def list(ctx):
    pass


@cli.command()
@click.pass_context
def refresh(ctx):
    pass


@cli.command()
@click.pass_context
def update(ctx):
    pass
