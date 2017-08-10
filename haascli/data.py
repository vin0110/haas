import click
from executor.ssh.client import RemoteCommand

from haascli.cluster import ClusterTopology
from haascli import debug, message


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.pass_context
def cli(ctx, **kwargs):
    """Data related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.argument('stack_name')
@click.pass_context
def save(ctx, stack_name):
    topology = ClusterTopology.parse(stack_name)
    s3_bucket = "osr-{}".format(stack_name)
    message("S3 bucket: {}", s3_bucket)

    RemoteCommand(topology.get_master_ip(),
                  'source ~/project-aws/init.sh; cd ~/project-aws; '
                  'hpcc_migrator --protocol s3 --s3_bucket {} save_cluster'.format(s3_bucket)).start()
    # @TODO: need to return exit code

@cli.command()
@click.argument('stack_from')
@click.argument('stack_to')
@click.pass_context
def restore(ctx, stack_from, stack_to):
    topology = ClusterTopology.parse(stack_to)
    s3_bucket = "osr-{}".format(stack_from)
    message("S3 bucket: {}", s3_bucket)

    RemoteCommand(topology.get_master_ip(),
                  'source ~/project-aws/init.sh; cd ~/project-aws; '
                  'hpcc_migrator --protocol s3 --s3_bucket {} restore_cluster'.format(s3_bucket)).start()
    # @TODO: need to return exit code


@cli.command()
@click.pass_context
def resize(ctx):
    pass
