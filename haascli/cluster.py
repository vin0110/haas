import click
import boto3
import executor
from executor.ssh.client import RemoteCommand



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
@click.option('-s', '--stack_name', default='myhpcc')
@click.pass_context
def cli(ctx, **kwargs):
    """Cluster related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.pass_context
def start(ctx):
    # @TODO: a cache mechanism would be better
    topology = ClusterTopology.parse(ctx.obj['stack_name'])
    # @TODO: after we finalize the AMI, we don't need to switch to the user's directory
    RemoteCommand(topology.get_master_ip(), 'source ~/project-aws/init.sh; cd ~/project-aws; hpcc service --action start').start()


@cli.command()
@click.pass_context
def stop(ctx):
    topology = ClusterTopology.parse(ctx.obj['stack_name'])
    RemoteCommand(topology.get_master_ip(), 'source ~/project-aws/init.sh; cd ~/project-aws; hpcc service --action stop').start()


@cli.command()
@click.pass_context
def restart(ctx):
    ctx.invoke(stop)
    ctx.invoke(start)

@cli.command()
@click.pass_context
def status(ctx):
    topology = ClusterTopology.parse(ctx.obj['stack_name'])
    RemoteCommand(topology.get_master_ip(), 'source ~/project-aws/init.sh; cd ~/project-aws; hpcc service --action status').start()
