import os
import time
import logging
import base64

import click
from executor.ssh.client import RemoteCommand
from .stack import get_ips

logger = logging.getLogger(__name__)

DEFAULT_BUCKET = 'hpcc_checkpoint'


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
    service_output = "/tmp/haas_data.out"

    # @TODO: if the required library is installed in system, the
    # init.sh can be removed @TODO: the path to checkpoint.py needs to
    # reflect the changes in auto_hpcc.sh

    master_ip = get_ips(stack_name, "MasterASG")[0]
    if bucket == None:
        try:
            bucket = ctx.obj['bucket']
        except KeyError:
            # use defaul bucket
            bucket = DEFAULT_BUCKET

    # didn't use RemoteCommand because I cannot make it work
    # base64 turns out to be an easy way to escape commands
    cmd = "$(nohup python3 /opt/haas/checkpoint.py {} save {} {} '{}'"\
          " > {} 2>&1 &)".format(
              resource_name, bucket, checkpoint_name, regex, service_output)
    if ctx.obj['exec']:
        os.system("ssh -i {} -l {} {} 'echo {} | base64 -d | bash'".format(
            ctx.obj['identity'],
            'ubuntu',
            master_ip,
            base64.b64encode(cmd.encode()).decode())
        )

        if ctx.obj['wait']:
            _wait_until_complete(master_ip, ctx.obj['identity'])
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
    master_ip = get_ips(stack_name, "MasterASG")[0]

    if bucket == None:
        try:
            bucket = ctx.obj['bucket']
        except KeyError:
            # use defaul bucket
            bucket = DEFAULT_BUCKET

    cmd = "$(nohup python3 /opt/haas/checkpoint.py {} restore {} {} '{}'" \
          " > {} 2>&1 &)".format(
        resource_name, bucket, checkpoint_name, regex, service_output)
    if ctx.obj['exec']:
        os.system("ssh -i {} -l {} {} 'echo {} | base64 -d | bash'".format(
            ctx.obj['identity'],
            'ubuntu',
            master_ip,
            base64.b64encode(cmd.encode()).decode())
        )

        if ctx.obj['wait']:
            _wait_until_complete(master_ip, ctx.obj['identity'])
    else:
        print('not executing `{}`'.format(cmd))


@cli.command()
@click.argument('stack_name')
@click.pass_context
def progress(ctx, stack_name):
    '''Check progress of checkpointing operation'''
    master_ip = get_ips(stack_name, "MasterASG")[0]

    cmd = RemoteCommand(master_ip,
                        'python3 /opt/haas/checkpoint.py '
                        '--name {} available; echo $?',
                        identity_file=ctx.obj['identity'],
                        ssh_user='ubuntu',
                        capture=True)
    if ctx.obj['exec']:
        cmd.start()
        if cmd.output == '0':
            print("No service is running")
        else:
            print('Data service is running....')
            RemoteCommand(master_ip, "tail -f /tmp/haas_data.out",
                          identity_file=ctx.obj['identity'],
                          ssh_user='ubuntu',
                          check=False).start()
    else:
        print('not executing `{}`'.format(cmd.command))


@cli.command()
@click.argument('stack-name')
@click.option('--regex', default='*', help='The regex (filename glob) to filter file path or workunit id')
@click.pass_context
def resize(ctx, stack_name, regex):
    topology = ClusterTopology.parse(stack_name)
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    cmd = "python3 /opt/haas/resize.py '{}'".format(regex)

    os.system("ssh -i {} -l {} {} 'echo {} | base64 -d | bash'".format(
        conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        conf.get(HaasConfigurationKey.HAAS_SSH_USER),
        topology.get_master_ip(),
        base64.b64encode(cmd.encode()).decode())
    )


def _wait_until_complete(master_ip, identity):
    while True:
        cmd = RemoteCommand(master_ip, "pgrep -f checkpoint.py",
                            identity_file=identity,
                            ssh_user='ubuntu',
                            capture=True, check=False)
        cmd.start()
        pid_list = cmd.output
        # print(pid_list, len(pid_list.splitlines()))
        if len(pid_list.splitlines()) > 0:
            print("Data service still processing")
            time.sleep(5)
        else:
            break
