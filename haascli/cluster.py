import click
from executor.ssh.client import RemoteCommand

from .stack import get_master_ip


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.pass_context
def cli(ctx, **kwargs):
    """Cluster related operations"""
    ctx.obj.update(kwargs)
    if 'identity' not in ctx.obj:
        print(click.style('must provide an identity file', fg='red'))
        ctx.abort()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def init(ctx, stack_name):
    master_ip = get_master_ip(stack_name)

    RemoteCommand(
        master_ip,
        'sudo -u hpcc -i bash /opt/haas/auto_hpcc.sh',
        identity_file=ctx.obj['identity'],
        ssh_user=ctx.obj['username']
    ).start()


def _run_service(ctx, stack_name, service):
    if ctx.obj['test']:
        master_ip = '127.0.0.1'
    else:
        # @TODO: a cache mechanism would be better
        try:
            master_ip = get_master_ip(stack_name)
        except KeyError as e:
            print(click.style(str(e), fg='red'))
            ctx.abort()

    # @TODO: after we finalize the AMI, we don't need to switch to the
    # user's directory
    cmd = RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a '
        'dafilesrv {}"'.format(service),
        identity_file=ctx.obj['identity'],
        ssh_user=ctx.obj['username'],
    )
    cmd2 = RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a '
        'hpcc-init {}"'.format(service),
        identity_file=ctx.obj['identity'],
        ssh_user=ctx.obj['username'],
    )
    if ctx.obj['test']:
        print('not executing `{}`'.format(cmd.command_line))
        print('not executing `{}`'.format(cmd2.command_line))
    else:
        cmd.start()
        cmd2.start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def start(ctx, stack_name):
    '''Start HPCC service on the cluster.'''
    _run_service(ctx, stack_name, 'start')


@cli.command()
@click.argument('stack-name')
@click.pass_context
def stop(ctx, stack_name):
    '''Stop HPCC services on the cluster.'''
    _run_service(ctx, stack_name, 'stop')


@cli.command()
@click.argument('stack-name')
@click.pass_context
def restart(ctx, stack_name):
    '''Restart HPCC services on the cluster.'''
    _run_service(ctx, stack_name, 'restart')


@cli.command()
@click.argument('stack-name')
@click.pass_context
def status(ctx, stack_name):
    '''Show status of the HPCC services.'''
    _run_service(ctx, stack_name, 'status')
