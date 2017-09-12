import logging
import click
from executor.ssh.client import RemoteCommand

from haascli.cluster import ClusterTopology

logger = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--bucket', default='hpcc_checkpoint')
@click.option('-r', '--resource', type=click.Choice(['dfs', 'workunit', 'dropzone']), default=None, help='HPCC resources')
@click.pass_context
def cli(ctx, **kwargs):
    """Data related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.argument('stack_name')
@click.argument('checkpoint_name')
@click.pass_context
def save(ctx, stack_name, checkpoint_name):
    resource_name = ctx.obj['resource']
    if not resource_name:
        print('Need to specify a resource')
        ctx.abort()

    topology = ClusterTopology.parse(stack_name)

    # @TODO: if the required library is installed in system, the init.sh can be removed
    # @TODO: the path to checkpoint.py needs to reflect the changes in auto_hpcc.sh
    RemoteCommand(topology.get_master_ip(),
                  'source ~/haas/scripts/init.sh;'
                  'nohup python ~/haas/scripts/checkpoint.py --name {} service_{} save < /dev/null > /dev/null 2>&1'.format(checkpoint_name, resource_name),
                  check=False).start()

@cli.command()
@click.argument('checkpoint_name')
@click.argument('stack_name')
@click.pass_context
def restore(ctx, checkpoint_name, stack_name):
    resource_name = ctx.obj['resource']
    if not resource_name:
        print('Need to specify a resource')
        ctx.abort()

    topology = ClusterTopology.parse(stack_name)

    RemoteCommand(topology.get_master_ip(),
                  'source ~/haas/scripts/init.sh;'
                  'haas checkpoint --name {} available;'
                  'if [ $? -ne 0 ]; then echo CheckpointService is running; else '
                  'nohup haas checkpoint --name {} service_{} restore < /dev/null > /dev/null 2>&1'
                  '; fi'.format(checkpoint_name, checkpoint_name, resource_name),
                  check=False).start()


@cli.command()
@click.argument('stack_name')
@click.pass_context
def progress(ctx, stack_name):
    topology = ClusterTopology.parse(stack_name)

    cmd = RemoteCommand(topology.get_master_ip(),
                        'source ~/haas/scripts/init.sh; haas checkpoint --name {} available; echo $?',
                        capture=True)
    cmd.start()
    if cmd.output == '0':
        print("No job are running")
    else:
        RemoteCommand(topology.get_master_ip(), "tail -f /tmp/haas_checkpoint.out", silent=True, check=False).start()


@cli.command()
@click.pass_context
def resize(ctx):
    pass
