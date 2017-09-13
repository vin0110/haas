import os
import time
import logging
import base64

import click
from executor.ssh.client import RemoteCommand

from haascli.cluster import ClusterTopology

logger = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--bucket', default='hpcc_checkpoint')
@click.option('-r', '--resource', type=click.Choice(['dfs', 'workunit', 'dropzone']), default=None, help='HPCC resources')
@click.option('--regex', default='*', help='The regex (filename glob) to filter file path or workunit id')
@click.option('--wait/--no-wait', default=True, help='Waiting for the operation to complete')
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

    service_output = "/tmp/haas_data.out"

    # @TODO: if the required library is installed in system, the init.sh can be removed
    # @TODO: the path to checkpoint.py needs to reflect the changes in auto_hpcc.sh
    # didn't use RemoteCommand because I cannot make it work
    # base64 turns out to be an easy way to escape commands
    cmd = "source /home/osr/haas/scripts/init.sh && $(nohup python /home/osr/haas/scripts/checkpoint.py --name {} service_{} save --regex '{}'> {} 2>&1 &)".format(checkpoint_name, resource_name, ctx.obj['regex'], service_output)
    os.system("ssh {} 'echo {} | base64 -d | bash'".format(topology.get_master_ip(), base64.b64encode(cmd.encode()).decode()))

    if ctx.obj['wait']:
        _wait_until_complete(topology.get_master_ip())


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

    service_output = "/tmp/haas_data.out"

    cmd = "source /home/osr/haas/scripts/init.sh && $(nohup python /home/osr/haas/scripts/checkpoint.py --name {} service_{} restore --regex '{}'> {} 2>&1 &)".format(checkpoint_name, resource_name, ctx.obj['regex'], service_output)
    os.system("ssh {} 'echo {} | base64 -d | bash'".format(topology.get_master_ip(), base64.b64encode(cmd.encode()).decode()))

    if ctx.obj['wait']:
        _wait_until_complete(topology.get_master_ip())


@cli.command()
@click.argument('stack_name')
@click.pass_context
def progress(ctx, stack_name):
    topology = ClusterTopology.parse(stack_name)

    cmd = RemoteCommand(topology.get_master_ip(),
                        'source ~/haas/scripts/init.sh; python /home/osr/haas/scripts/checkpoint.py --name {} available; echo $?',
                        capture=True)
    cmd.start()
    if cmd.output == '0':
        print("No service is running")
    else:
        print('Data service is running....')
        RemoteCommand(topology.get_master_ip(), "tail -f /tmp/haas_data.out", check=False).start()


@cli.command()
@click.pass_context
def resize(ctx):
    pass


def _wait_until_complete(master_ip):
    while True:
        cmd = RemoteCommand(master_ip, "pgrep -f checkpoint.py", capture=True, check=False)
        cmd.start()
        pid_list = cmd.output
        # print(pid_list, len(pid_list.splitlines()))
        if len(pid_list.splitlines()) > 0:
            print("Data service still processing")
            time.sleep(5)
        else:
            break
