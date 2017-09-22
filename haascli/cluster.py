import sys
import logging
from io import StringIO

import click
from executor.ssh.client import RemoteCommand
import boto3

from .stack import get_ips
from .stack import parameters as stack_parameters


logger = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.pass_context
def cli(ctx, **kwargs):
    """Cluster related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.argument('stack-name')
@click.pass_context
def init(ctx, stack_name):
    # @TODO: this is a lazy implementation unless we refactor the stack implementation which
    #        initializes the boto client in cli
    optargs = {}
    if ctx.obj['region']:
        optargs['region_name'] = ctx.obj['region']
    if ctx.obj['key']:
        optargs['aws_access_key_id'] = ctx.obj['key']
    if ctx.obj['secret']:
        optargs['aws_secret_access_key_id'] = ctx.obj['secret']

    # supress the output
    with CaptureOutput():
        ctx.obj['client'] = boto3.client('cloudformation', **optargs)
        cluster_params = ctx.invoke(stack_parameters, stack_name=stack_name)

    master_ip = get_ips(stack_name, "MasterASG", public=True)[0]
    # @TODO: is the master always a part of the HPCC Systems cluster?
    ips = get_ips(stack_name, "MasterASG", public=False) + get_ips(stack_name, "SlaveASG", public=False)

    try:
        RemoteCommand(
            master_ip,
            'python3 /opt/haas/cluster.py init {ThorNodes} {RoxieNodes} {SupportNodes} {SlavesPerNode} "{ip_list}"'.format(
                ip_list=",".join(ips),
                **cluster_params
            ),
            identity_file=ctx.obj['identity'],
            ssh_user='ubuntu',
            silent=True, check=True
        ).start()
    except Exception as e:
        logger.error('Unable to initialize the HPCC Systems cluster: ' + str(e))
        ctx.abort()
    print('Successfully initialize the HPCC cluster')


@cli.command()
@click.argument('stack-name')
@click.pass_context
def start(ctx, stack_name):
    # @TODO: a cache mechanism would be better
    master_ip = get_ips(stack_name, "MasterASG")[0]

    # @TODO: after we finalize the AMI, we don't need to switch to the
    # user's directory
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv start"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init start"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def stop(ctx, stack_name):
    master_ip = get_ips(stack_name, "MasterASG")[0]
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv stop"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init stop"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def restart(ctx, stack_name):
    master_ip = get_ips(stack_name, "MasterASG")[0]
    RemoteCommand(
        master_ip,
        'sudo bash -c '
        '"/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv restart"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c '
        '"/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init restart"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def status(ctx, stack_name):
    master_ip = get_ips(stack_name, "MasterASG")[0]
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv status"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init status"',
        identity_file=ctx.obj['identity'],
        ssh_user='ubuntu'
    ).start()


class CaptureOutput(list):
    '''Taken from http://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
    '''
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        sys.stdout = self._stdout