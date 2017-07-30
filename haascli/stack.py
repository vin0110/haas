import click


@click.group()
@click.pass_context
def cli(ctx, **kwargs):
    """Stack related operations
    """
    ctx.obj = kwargs


@cli.command()
@click.pass_context
def create(ctx):
    pass


@cli.command()
@click.pass_context
def list(ctx):
    pass


@cli.command()
@click.pass_context
def destroy(ctx):
    pass

@cli.command()
@click.pass_context
def update(ctx):
    pass
