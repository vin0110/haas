import os
import json

import click
import boto3
import yaml


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--config', default='.')
@click.pass_context
def cli(ctx, **kwargs):
    """Stack related operations
    """
    ctx.obj.update(kwargs)


@cli.command()
@click.argument('stack_name')
@click.argument('config_name')
@click.pass_context
def create(ctx, stack_name, config_name):
    config_path = os.path.join(ctx.obj['config_dir'], '{}.yaml'.format(config_name))
    with open(config_path, 'r') as f:
        config_object = yaml.load(f)

    # hard coded for now
    # @TODO: need to decide how to format the source code
    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "templates", "haas_cft.json")

    stack_id = None
    client = boto3.client('cloudformation')
    try:
        with open(template_path, 'r') as f:
            response = client.create_stack(
                StackName=stack_name,
                TemplateBody=f.read(),
                Parameters=[
                    {
                        'ParameterKey': 'KeyName',
                        'ParameterValue': config_object['key'],
                    },
                    {
                        'ParameterKey': 'ClusterSize',
                        'ParameterValue': str(config_object['slave_node']),
                    },
                    {
                        'ParameterKey': 'MasterInstanceType',
                        'ParameterValue': config_object['master_instance_type'],
                    },
                    {
                        'ParameterKey': 'SlaveInstanceType',
                        'ParameterValue': config_object['slave_instance_type'],
                    }
                ],
                Capabilities=['CAPABILITY_IAM'],
            )
            stack_id = response['StackId'] if 'StackId' in response else None
    except Exception as e:
        # @TODO: needs better exception handling
        print("Uable to complete stack creation")

    print("StackId:", stack_id)


@cli.command()
@click.pass_context
def list(ctx):
    pass


@cli.command()
@click.pass_context
def destroy(ctx):
    pass

@cli.command()
@click.pass_context
def update(ctx):
    pass
