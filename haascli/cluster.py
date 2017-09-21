import click
from executor.ssh.client import RemoteCommand

from .config import HaasConfigurationManager, HaasConfigurationKey
from .stack import get_ip


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.pass_context
def cli(ctx, **kwargs):
    """Cluster related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.argument('stack-name')
@click.pass_context
def start(ctx, stack_name):
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    # @TODO: a cache mechanism would be better
    master_ip = get_ip(stack_name, "MasterASG")

    # @TODO: after we finalize the AMI, we don't need to switch to the user's directory
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv start"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init start"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def stop(ctx, stack_name):
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    master_ip = get_ip(stack_name, "MasterASG")
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv stop"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init stop"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def restart(ctx, stack_name):
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    master_ip = get_ip(stack_name, "MasterASG")
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv restart"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init restart"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def status(ctx, stack_name):
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    master_ip = get_ip(stack_name, "MasterASG")
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv status"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        master_ip,
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init status"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
