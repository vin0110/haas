import os
# import json

import click
import boto3
import yaml
import requests
import haascli
from botocore.exceptions import ClientError, PartialCredentialsError


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--config', default='.')
@click.pass_context
def cli(ctx, **kwargs):
    """Stack related operations
    """

    optargs = {}
    if ctx.obj['region']:
        optargs['region_name'] = ctx.obj['region']
    if ctx.obj['key']:
        optargs['aws_access_key_id'] = ctx.obj['key']
    if ctx.obj['secret']:
        optargs['aws_secret_access_key_id'] = ctx.obj['secret']
    if ctx.obj['debug']:
        print('aws settings:\n',
              '\n'.join(['{}={}'.format(k, v) for k, v in optargs.items()]))

    # open the client here instead of in all commands
    if ctx.obj['exec']:
        try:
            ctx.obj['client'] = boto3.client('cloudformation', **optargs)
        except (ClientError, PartialCredentialsError) as e:
            haascli.error(str(e))
            ctx.abort()


@cli.command()
@click.argument('stack_name')
@click.option('-f', '--config_file')
@click.option('-p', '--parameter', multiple=True)
@click.pass_context
def create(ctx, stack_name, config_file, parameter):
    '''Creates an AWS stack
    '''
    debug = ctx.obj['debug']
    if debug:
        click.echo('haas stack create stack_name={}'.format(stack_name))
        if not ctx.obj['exec']:
            haascli.warning('no exec mode')

    parameters = {}
    if config_file:
        config_path = os.path.join(ctx.obj['config_dir'], config_file)
        try:
            f = open(config_path, 'r')
            # @TODO: assuming all config files are yaml
            parameters = yaml.load(f)
        except IOError as e:
            haascli.error(str(e))
            ctx.abort()
    else:
        for param in parameter:
            try:
                key, val = param.split('=')
            except IndexError:
                val = True
            if key in parameters:
                haascli.warning('overwriting {} to {} was {}'.format(
                    key, val, parameters[key]))
            parameters[key] = val

    try:
        # template_url MUST be defined; but it isn't a parameter
        template_url = parameters['template_url']
        del parameters['template_url']
    except KeyError as e:
        haascli.error('must define template_url')
        ctx.abort()

    if debug:
        click.echo('template url is {}'.format(template_url))

        for k, v in parameters.items():
            click.echo('parameter {} is {}'.format(k, v))

    stack_id = None

    # prepare parameters for boto call
    parameter_list = []
    for param in parameters:
        parameter_list.append(dict(ParameterKey=param,
                                   ParameterValue=parameters[param]))
    if debug:
        msg = '\tStackName={}\n\tTemplateUrl={}\n'\
              '\tParameters={}\n'\
              '\tCapabilities=[\'CAPABILITY_IAM\']'\
              .format(stack_name, template_url, parameter_list)
        click.echo(msg)

    try:
        client = ctx.obj['client']
        if template_url.startswith('http'):
            if 's3' in template_url:
                response = client.create_stack(
                    StackName=stack_name,
                    TemplateUrl=template_url,
                    Parameters=parameter_list,
                    Capabilities=['CAPABILITY_IAM'],
                )
                # so that we can have one clause for TemplateBody version
                body = False
            else:
                # fetch url contents
                r = requests.get(template_url, timeout=5.0)
                body = r.text
        else:
            if template_url.startswith('file:'):
                f = template_url[5].strip('/')
            else:
                f = template_url
            body = open(f, 'r').read()

        if body:
            # if body is false create_stack was called above
            response = client.create_stack(
                StackName=stack_name,
                TemplateBody=body,
                Parameters=parameter_list,
                Capabilities=['CAPABILITY_IAM'],
            )

        if haascli.bad_response(response):
            ctx.abort()
        stack_id = response['StackId'] if 'StackId' in response else None
        click.echo("StackId:", str(stack_id))

    except IOError as e:
        haascli.error(str(e))
        ctx.abort()
    except requests.exceptions.RequestException as e:
        haascli.error(str(e))
        ctx.abort()
    except ClientError as e:
        haascli.error(str(e))
        ctx.abort()
    except KeyError as e:
        if e.args[0] == 'client':
            haascli.warning('not executing')
        else:
            raise KeyError(e)


@cli.command()
@click.option('-l', '--long', is_flag=True)
@click.option('-f', '--filter', multiple=True)
@click.pass_context
def list(ctx, long, filter):
    '''lists stacks
    '''
    if ctx.obj['debug']:
        click.echo('haas stack list long={} filter={}'.format(long, filter))

    try:
        client = ctx.obj['client']
        if filter:
            response = client.list_stacks(StackStatusFilter=filter)
        else:
            response = client.list_stacks()
        if haascli.bad_response(response):
            ctx.abort()

        for stack in response['StackSummaries']:
            print(stack['StackName'], 'status:', stack['StackStatus'])
            if long:
                print('\tTemplate:', stack['TemplateDescription'])
                print('\tId:', stack['StackId'])
                print('\tCreated:', str(stack['CreationTime']))
                if 'DeletionTime' in stack:
                    print('\tDeleted:', str(stack['DeletionTime']))
    except ClientError as e:
        haascli.error(str(e))
        ctx.abort()
    except KeyError as e:
        if e.args[0] == 'client':
            haascli.warning('not executing')
        else:
            raise KeyError(e)


@cli.command()
@click.argument('stack-name')
@click.pass_context
def delete(ctx, stack_name):
    '''Delete stack with given name or stack id
    '''
    if ctx.obj['debug']:
        click.echo('haas stack delete stack_name={}'.format(stack_name))

    try:
        client = ctx.obj['client']
        response = client.delete_stack(StackName=stack_name)
        if haascli.bad_response(response):
            ctx.abort()
    except ClientError as e:
        haascli.error(str(e))
        ctx.abort()
    except KeyError as e:
        if e.args[0] == 'client':
            haascli.warning('not executing')
        else:
            raise KeyError(e)


@cli.command()
@click.pass_context
def update(ctx):
    pass
