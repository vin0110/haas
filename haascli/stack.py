import os
import logging

import click
import boto3
import yaml
import requests
from botocore.exceptions import ClientError, PartialCredentialsError

from haascli import bad_response

logger = logging.getLogger(__name__)


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
    logger.debug('aws settings:\n{}'.format(
                 '\n'.join(['{}={}'.format(k, v) for k, v in optargs.items()])))

    # open the client here instead of in all commands
    if ctx.obj['exec']:
        try:
            ctx.obj['client'] = boto3.client('cloudformation', **optargs)
        except (ClientError, PartialCredentialsError) as e:
            logger.error(str(e))
            ctx.abort()


@cli.command()
@click.argument('stack_name')
@click.option('-f', '--config_file')
@click.option('-p', '--parameter', multiple=True)
@click.option('--wait/--no-wait', default=False)
@click.pass_context
def create(ctx, stack_name, config_file, parameter, wait):
    '''Creates an AWS stack
    '''
    logger.debug('haas stack create stack_name={}'.format(stack_name))
    if not ctx.obj['exec']:
        logger.warning('no exec mode')

    parameters = {}
    if config_file:
        config_path = os.path.join(ctx.obj['config_dir'], config_file)
        try:
            f = open(config_path, 'r')
            # @TODO: assuming all config files are yaml
            parameters = yaml.load(f)
        except IOError as e:
            logger.error(str(e))
            ctx.abort()
    else:
        for param in parameter:
            try:
                key, val = param.split('=')
            except IndexError:
                val = True
            if key in parameters:
                logger.warning('overwriting {} to {} was {}'.format(
                    key, val, parameters[key]))
            parameters[key] = val

    try:
        # template_url MUST be defined; but it isn't a parameter
        template_url = parameters['template_url']
        del parameters['template_url']
    except KeyError as e:
        logger.error('must define template_url')
        ctx.abort()

    if ctx.obj['debug']:
        logger.debug('template url is {}'.format(template_url))

        for k, v in parameters.items():
            logger.debug('parameter {} is {}'.format(k, v))

    stack_id = None

    # prepare parameters for boto call
    parameter_list = []
    for param in parameters:
        parameter_list.append(dict(ParameterKey=param,
                                   ParameterValue=parameters[param]))
    logger.debug('\tStackName={}\n\tTemplateUrl={}\n'
                 '\tParameters={}\n'
                 '\tCapabilities=[\'CAPABILITY_IAM\']'
                 .format(stack_name, template_url, parameter_list))

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
            if template_url.startswith('file://'):
                fn = template_url[7:]
            else:
                fn = template_url
                if not os.path.isfile(fn):
                    # didn't find the file; look in config_dir
                    fn = os.path.join(ctx.obj['config_dir'], fn)
            # change this to have explict close because moto
            # was generating a warning during testing
            # `ResourceWarning: unclosed file <_io.TextIOWrapper ...`
            f = open(fn, 'r')
            body = f.read()
            f.close()

        if body:
            # if body is false create_stack was called above
            response = client.create_stack(
                StackName=stack_name,
                TemplateBody=body,
                Parameters=parameter_list,
                Capabilities=['CAPABILITY_IAM'],
            )

        if bad_response(response):
            ctx.abort()
        stack_id = response['StackId'] if 'StackId' in response else None
        print("StackId:", str(stack_id))

        if wait:
            waiter = client.get_waiter('stack_create_complete')
            waiter.wait(StackName=stack_name)

    except IOError as e:
        logger.error(str(e))
        ctx.abort()
    except requests.exceptions.RequestException as e:
        logger.error(str(e))
        ctx.abort()
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        ctx.abort()
    except KeyError as e:
        if e.args[0] == 'client':
            logger.warning('not executing')
        else:
            raise KeyError(e)


@cli.command()
@click.option('-l', '--long', is_flag=True)
@click.option('-f', '--filter', multiple=True)
@click.pass_context
def list(ctx, long, filter):
    '''lists stacks
    '''
    logger.debug('haas stack list long={} filter={}'.format(long, filter))

    try:
        client = ctx.obj['client']
        if filter:
            response = client.list_stacks(StackStatusFilter=filter)
        else:
            response = client.list_stacks()
        if bad_response(response):
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
        logger.error(e.response['Error']['Message'])
        ctx.abort()
    except KeyError as e:
        if e.args[0] == 'client':
            logger.warning('not executing')
        else:
            raise KeyError(e)


@cli.command()
@click.argument('stack-name')
@click.option('--wait/--no-wait', default=False)
@click.pass_context
def delete(ctx, stack_name, wait):
    '''Delete stack with given name or stack id
    '''
    logger.debug('haas stack delete stack_name={}'.format(stack_name))

    try:
        client = ctx.obj['client']
        response = client.delete_stack(StackName=stack_name)
        if wait:
            waiter = client.get_waiter('stack_delete_complete')
            waiter.wait(StackName=stack_name)

        if bad_response(response):
            ctx.abort()
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        ctx.abort()
    except KeyError as e:
        if e.args[0] == 'client':
            logger.warning('not executing')
        else:
            raise KeyError(e)


@cli.command()
@click.argument('stack-name')
@click.pass_context
def events(ctx, stack_name):
    '''Display events for a stack
    Events might be delivered in more than one message
    '''
    logger.debug('haas stack delete stack_name={}'.format(stack_name))

    try:
        client = ctx.obj['client']
        paginator = client.get_paginator('describe_stack_events')
        events_iter = paginator.paginate(StackName=stack_name)

        for events in events_iter:
            for event in events['StackEvents']:
                print('%-20s %-40s %s' %
                      (event['ResourceStatus'],
                       event['ResourceType'],
                       event['Timestamp'].strftime('%Y.%m.%d-%X')))
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        ctx.abort()
    except KeyError as e:
        if e.args[0] == 'client':
            logger.warning('not executing')
            return
        else:
            raise KeyError(e)


@cli.command()
@click.pass_context
def update(ctx):
    pass
