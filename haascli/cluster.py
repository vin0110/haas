import click
import boto3
import executor
from executor.ssh.client import RemoteCommand

from haascli.config import HaasConfigurationManager, HaasConfigurationKey


class ClusterTopology(object):
    @staticmethod
    def parse(stack_name):
        client = boto3.client('cloudformation')
        client_autoscaling = boto3.client('autoscaling')
        client_ec2 = boto3.client('ec2')
        response = client.describe_stacks(
            StackName=stack_name,
            # NextToken='test',
        )
        assert len(response['Stacks']) == 1

        # not sure whether the following implementation supports multiple nodes in autoscaling groups
        master_ip = None
        stack_record = response['Stacks'][0]
        result = client.list_stack_resources(StackName=stack_record['StackName'])

        for stack_resource in result['StackResourceSummaries']:
            if not (stack_resource['ResourceType'] == 'AWS::AutoScaling::AutoScalingGroup' and
                    stack_resource['LogicalResourceId'] == 'MasterASG'):
                continue

            instance_list = client_autoscaling.describe_auto_scaling_instances()
            instance_id_list = []
            for instance in instance_list['AutoScalingInstances']:
                if instance['AutoScalingGroupName'] == stack_resource['PhysicalResourceId']:
                    instance_id_list.append(instance['InstanceId'])

            ec2_instance_list = client_ec2.describe_instances(InstanceIds=instance_id_list)
            # not sure any issue in this way
            master_ip = ec2_instance_list['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']

        return ClusterTopology(master_ip)

    def __init__(self, master_ip):
        self.master_ip = master_ip

    def get_master_ip(self):
        return self.master_ip


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
    topology = ClusterTopology.parse(stack_name)
    # @TODO: after we finalize the AMI, we don't need to switch to the user's directory
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv start"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init start"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def stop(ctx, stack_name):
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    topology = ClusterTopology.parse(stack_name)
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv stop"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init stop"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def restart(ctx, stack_name):
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    topology = ClusterTopology.parse(stack_name)
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv restart"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init restart"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()


@cli.command()
@click.argument('stack-name')
@click.pass_context
def status(ctx, stack_name):
    conf = HaasConfigurationManager().get(ctx.obj['config'])
    topology = ClusterTopology.parse(stack_name)
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a dafilesrv status"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
    RemoteCommand(
        topology.get_master_ip(),
        'sudo bash -c "/opt/HPCCSystems/sbin/hpcc-run.sh -a hpcc-init status"',
        identity_file=conf.get(HaasConfigurationKey.HAAS_SSH_KEY),
        ssh_user=conf.get(HaasConfigurationKey.HAAS_SSH_USER)
    ).start()
