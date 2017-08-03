import os
import glob

import click
import yaml


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.pass_context
def cli(ctx, **kwargs):
    """Config related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.pass_context
def list(ctx):
    # TODO: need a elaborate approach later
    config_list = [f.split('.')[0] for f in os.listdir(os.path.join(ctx.obj['config_dir'])) if 'yaml' in f]
    print(config_list)


@cli.command()
@click.pass_context
def refresh(ctx):
    pass


@cli.command()
@click.pass_context
def update(ctx):
    pass


@cli.command()
@click.argument('name')
@click.option('--key', type=str, default='haas', help="The key profile name configured in AWS")
@click.option('--master_node', type=int, default=1, help="The number of cluster-wider service nodes")
@click.option('--slave_node', type=int, default=1, help="The number of Thor/Roxie nodes")
@click.option('--master_instance_type', type=click.Choice(['t2.micro', 'c4.large']), default='t2.micro', help="The instance type of the master nodes")
@click.option('--slave_instance_type', type=click.Choice(['t2.micro', 'c4.large']), default='t2.micro', help="The instance type of the master nodes")
@click.option('--ebs_volume_size', type=int, default=20, help="The size of the EBS volume")
@click.pass_context
def new(ctx, name, key, master_node, slave_node, master_instance_type, slave_instance_type, ebs_volume_size):
    config = {
        'key': key,
        'master_node': master_node,
        'slave_node': slave_node,
        'master_instance_type': master_instance_type,
        'slave_instance_type': slave_instance_type,
        'ebs_volume_size': ebs_volume_size,
    }
    with open(os.path.join(ctx.obj['config_dir'], '{}.yaml'.format(name)), 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
