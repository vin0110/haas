import os
import time
import logging
import base64

import click
from executor.ssh.client import RemoteCommand

from haascli import Defaults
from .stack import get_master_ip

logger = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--wait/--no-wait', default=True,
              help='Waiting for the operation to complete')
@click.pass_context
def cli(ctx, **kwargs):
    """Data related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.argument('stack-name')
@click.argument('resource-name',
                type=click.Choice(['dfs', 'wu', 'dz']))
@click.argument('checkpoint-name')
@click.option('--regex', default='*',
              help='The regex (filename glob) to filter file path or '
              'workunit id')
@click.option('-b', '--bucket')
@click.pass_context
def save(ctx, stack_name, resource_name, checkpoint_name, regex, bucket):
    '''Save data to S3'''
    service_output = "/tmp/haas_data.out"

    # @TODO: if the required library is installed in system, the
    # init.sh can be removed @TODO: the path to checkpoint.py needs to
    # reflect the changes in auto_hpcc.sh

    master_ip = get_master_ip(stack_name)
    if bucket is None:
        try:
            bucket = ctx.obj['bucket']
        except KeyError:
            # use defaul bucket
            bucket = Defaults['bucket']

    # didn't use RemoteCommand because I cannot make it work
    # base64 turns out to be an easy way to escape commands
    cmd = "$(nohup python3 /opt/haas/checkpoint.py {} save {} {} '{}'" \
          " > {} 2>&1 &)".format(resource_name, bucket, checkpoint_name, regex, service_output)
    if not ctx.obj['test']:
        os.system("ssh -i {} -l {} {} 'echo {} | base64 -d | bash'".format(
            ctx.obj['identity'],
            ctx.obj['username'],
            master_ip,
            base64.b64encode(cmd.encode()).decode())
        )

        if ctx.obj['wait']:
            _wait_until_complete(master_ip, ctx.obj['identity'],
                                 ctx.obj['username'])
    else:
        print('not executing `{}`'.format(cmd))


@cli.command()
@click.argument('checkpoint-name')
@click.argument('resource-name',
                type=click.Choice(['dfs', 'wu', 'dz']))
@click.argument('stack-name')
@click.option('--regex', default='*',
              help='The regex (filename glob) to filter file path or workunit '
              'id')
@click.option('-b', '--bucket')
@click.pass_context
def restore(ctx, checkpoint_name, resource_name, stack_name, regex, bucket):
    '''Restore data from S3'''
    service_output = "/tmp/haas_data.out"
    master_ip = get_master_ip(stack_name)

    if bucket is None:
        try:
            bucket = ctx.obj['bucket']
        except KeyError:
            # use defaul bucket
            bucket = Defaults['bucket']

    cmd = "$(nohup python3 /opt/haas/checkpoint.py {} restore {} {} '{}'" \
          " > {} 2>&1 &)".format(resource_name, bucket, checkpoint_name, regex, service_output)
    if not ctx.obj['test']:
        os.system("ssh -i {} -l {} {} 'echo {} | base64 -d | bash'".format(
            ctx.obj['identity'],
            ctx.obj['username'],
            master_ip,
            base64.b64encode(cmd.encode()).decode())
        )

        if ctx.obj['wait']:
            _wait_until_complete(master_ip, ctx.obj['identity'],
                                 ctx.obj['username'])
    else:
        print('not executing `{}`'.format(cmd))


@cli.command()
@click.argument('stack_name')
@click.pass_context
def progress(ctx, stack_name):
    '''Check progress of checkpointing operation'''
    master_ip = get_master_ip(stack_name)

    cmd = RemoteCommand(master_ip,
                        'python3 /opt/haas/checkpoint.py '
                        '--name {} available; echo $?',
                        identity_file=ctx.obj['identity'],
                        ssh_user=ctx.obj['username'],
                        capture=True)
    if ctx.obj['test']:
        print('not executing `{}`'.format(cmd.command))
    else:
        cmd.start()
        if cmd.output == '0':
            print("No service is running")
        else:
            print('Data service is running....')
            RemoteCommand(master_ip, "tail -f /tmp/haas_data.out",
                          identity_file=ctx.obj['identity'],
                          ssh_user=ctx.obj['username'],
                          check=False).start()


@cli.command()
@click.argument('stack-name')
@click.option('--regex', default='*',
              help='The regex (filename glob) to filter file path or '
              'workunit id')
@click.pass_context
def resize(ctx, stack_name, regex):
    '''Distribute files in DFS from the restored size to the current cluster
    size'''
    master_ip = get_master_ip(stack_name)
    cmd = "python3 /opt/haas/resize.py '{}'".format(regex)

    if ctx.obj['test']:
        print('not executing `{}`'.format(cmd))
    else:
        os.system("ssh -i {} -l {} {} 'echo {} | base64 -d | bash'".format(
            ctx.obj['identity'],
            ctx.obj['username'],
            master_ip,
            base64.b64encode(cmd.encode()).decode())
        )
        if ctx.obj['wait']:
            _wait_until_complete(master_ip, ctx.obj['identity'],
                                 ctx.obj['username'])


def _wait_until_complete(master_ip, identity, username):
    while True:
        cmd = RemoteCommand(master_ip, "pgrep -f checkpoint.py",
                            identity_file=identity,
                            ssh_user=username,
                            capture=True, check=False)
        cmd.start()
        pid_list = cmd.output
        # print(pid_list, len(pid_list.splitlines()))
        if len(pid_list.splitlines()) > 0:
            print("Data service still processing")
            time.sleep(5)
        else:
            break
