import os
import sys
import logging

import click
import boto3
import requests
from ruamel.yaml import YAML

from botocore.exceptions import ClientError, PartialCredentialsError

from haascli import bad_response

logger = logging.getLogger(__name__)


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--config', default='.')
@click.pass_context
def cli(ctx, **kwargs):
    """Stack related operations"""

    optargs = {}
    if ctx.obj['region']:
        optargs['region_name'] = ctx.obj['region']
    if ctx.obj['key']:
        optargs['aws_access_key_id'] = ctx.obj['key']
    if ctx.obj['secret']:
        optargs['aws_secret_access_key_id'] = ctx.obj['secret']
    if optargs:
        logger.debug('aws settings:\n{}'.format(
            '\n'.join(['{}={}'.format(k, v) for k, v in optargs.items()])))

    # open the client here instead of in all commands
    if ctx.obj['exec']:
        try:
            ctx.obj['client'] = boto3.client('cloudformation', **optargs)
        except (ClientError, PartialCredentialsError) as e:
            logger.error('AWS Credentials: ' + str(e))
            ctx.abort()


@cli.command()
@click.argument('stack_name')
@click.option('-f', '--config_file')
@click.option('-p', '--parameter', multiple=True)
@click.option('--wait/--no-wait', default=False)
@click.pass_context
def create(ctx, stack_name, config_file, parameter, wait):
    '''Creates an AWS stack'''

    logger.debug('haas stack create stack_name={}'.format(stack_name))
    if not ctx.obj['exec']:
        logger.warning('no exec mode')

    parameters = {}
    if config_file:
        f = None
        if config_file[0] == '/':
            # assume it is an absolute path
            config_path = config_file
        elif config_file[0] == '~':
            # expand user
            components = config_file.split('/')
            config_path = os.path.join(
                os.path.expanduser(components[0], *components[1:]))
        elif config_file[0] == '.':
            # relative path
            config_path = os.path.join(*config_file.split())
        else:
            # try relative path; then try config directory
            try:
                f = open(config_file, 'r')
            except IOError:
                config_path = os.path.join(ctx.obj['config_dir'],
                                           'config',
                                           config_file)

        if not f:
            try:
                f = open(config_path, 'r')
                # @TODO: assuming all config files are yaml
            except IOError as e:
                print(click.style(
                    'ERROR: Could not open config file: {}'.format(str(e)),
                    fg='red'))
                ctx.abort()
        yaml = YAML()
        parameters = yaml.load(f)

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
        print(click.style('ERROR: Must define template_url', fg='red'))
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
        if 'StackId' in response:
            stack_id = response['StackId']
            print("StackId:", stack_id)
            logger.info('created stack %s (%s)', stack_name, stack_id)
        else:
            msg = 'no stackid response from create_stack'
            print(click.style(msg, fg='yellow'))
            logger.warning(msg)

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
@click.option('-a', '--all', is_flag=True,
              help="shows deleted stacks as well")
@click.option('-f', '--filter', multiple=True,
              help='Filter is a string. For valid filters see '
              'https://docs.aws.amazon.com/AWSCloudFormation/latest/'
              'APIReference/API_ListStacks.html')
@click.pass_context
def list(ctx, long, all, filter):
    '''Lists stacks
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
            if not all and stack['StackStatus'] == 'DELETE_COMPLETE':
                continue
            print("%-30s %s" % (stack['StackName'], stack['StackStatus'], ))
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
    '''Display events for a stack'''
    logger.debug('haas stack delete stack_name={}'.format(stack_name))

    # Events might be delivered in more than one message, so use a
    # paginator
    try:
        client = ctx.obj['client']
        paginator = client.get_paginator('describe_stack_events')
        events_iter = paginator.paginate(StackName=stack_name)

        fmt = '%-20s %-40s %s'
        for events in events_iter:
            for event in events['StackEvents']:
                status = event['ResourceStatus']
                tup = (status,
                       event['ResourceType'],
                       event['Timestamp'].strftime('%Y.%m.%d-%X'), )
                msg = fmt % tup
                if "FAILED" in status:
                    msg = click.style(msg, fg='red')
                print(msg)
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
@click.argument('stack-name')
@click.option('-g', '--group', default="MasterASG",
              help='name of auto-scaling group (default: "MasterASG")')
@click.option('-a', '--all', is_flag=True,
              help="show al ips")
@click.pass_context
def ip(ctx, stack_name, group, all):
    '''Return public IP address for EC2 instances.
    By default shows only the first instance in MasterASG.
    '''
    # Must walk a very complex path of ids and dictionaries.
    # first get dictionary describing asg, from which we exact
    # the 'PhysicalResourceId'
    asg_name = group
    myasg = ctx.obj['client'].describe_stack_resource(
        StackName=stack_name, LogicalResourceId=asg_name)

    # create an ASG client to get group dictionaries, from which we
    # exact the ec2 instance ids
    asg = boto3.client('autoscaling')
    groups = asg.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            myasg['StackResourceDetail']['PhysicalResourceId']])
    try:
        instance_ids = groups['AutoScalingGroups'][0]['Instances']
    except IndexError:
        print(click.style('ASG {} has no instances'.format(group), fg='red'))
        ctx.abort()

    # create ec2 client to get instance dictionaries
    ec2 = boto3.client('ec2')
    for instance_dict in instance_ids:
        instance_id = instance_dict['InstanceId']
        instance = ec2.describe_instances(InstanceIds=[instance_id])
        print(instance['Reservations'][0]['Instances'][0]
              ['NetworkInterfaces'][0]['PrivateIpAddresses'][0]
              ['Association']['PublicIp'])
        if not all:
            break


@cli.command()
@click.argument('stack-name')
@click.option('-l', '--long', is_flag=True)
@click.pass_context
def resources(ctx, stack_name, long):
    '''List all resources assigned to a stack'''

    res = ctx.obj['client'].describe_stack_resources(StackName=stack_name)
    resources = res['StackResources']

    if long:
        fmt = "LogicalResourceId: {LogicalResourceId}\n"\
              "\tPhysicalResourceId: {PhysicalResourceId}\n"\
              "\tResourceStatus: {ResourceStatus}\n"\
              "\tResourceType: {ResourceType}\n"\
              "\tStackId: {StackId}\n"\
              "\tStackName: {StackName}\n"\
              "\tTimestamp: {Timestamp}"
    else:
        fmt = "{LogicalResourceId:24} {ResourceType:37} {ResourceStatus:18}"

    for resource in resources:
        print(fmt.format(**resource))


@cli.command()
@click.argument('template-url')
@click.option('-c', '--configure', is_flag=True)
@click.pass_context
def template(ctx, template_url, configure):
    '''Show parameters in given parameter or interactively create YAML
    that can be copied into a file.'''
    try:
        summary = getTemplateSummary(ctx.obj['client'], template_url)
    except KeyError as e:
        print(click.style(str(e), fg='red'))
        ctx.abort()

    if configure:
        yaml = YAML()
        configuration = {}

        configuration['template_url'] = template_url

        for param in summary['Parameters']:
            print('Parameter: {}'.format(param['ParameterKey']))
            if "Description" in param:
                print('\t{}'.format(param['Description']))
            if "ParameterConstraints" in param:
                print('\tConstraints: {}'.format(
                    param['ParameterConstraints']))
            print('\t{}'.format(param['ParameterType']))
            if "DefaultValue" in param:
                ans = input('default is "{}" change [y/N]? '.format(
                    param['DefaultValue']))
                if ans.lower() in ['y', 'yes']:
                    value = input("new value: ")
                else:
                    value = param['DefaultValue']
            else:
                value = input("set value: ")
            # assume it is a scalar that appears a string
            configuration[param['ParameterKey']] = str(value)

        yaml.dump(configuration, sys.stdout)
    else:
        fmt = "{ParameterKey:30} {ParameterType:30} {DefaultValue}"
        print(fmt.format(**dict(ParameterKey="Name", ParameterType="Type",
                                DefaultValue="Default")))
        print(fmt.format(**dict(ParameterKey="-"*4, ParameterType="-"*4,
                                DefaultValue="-"*7)))
        for param in summary['Parameters']:
            if "DefaultValue" not in param:
                param["DefaultValue"] = ''
            print(fmt.format(**param))


############################################
# support routines
############################################
def getTemplateBody(template_url):
    '''Returns the template body from the given URN'''
    local_prefix = 'file://'
    try:
        if template_url.startswith('http'):
            r = requests.get(template_url, allow_redirects=True)
            if r.status_code != 200:
                raise KeyError('invalid URL (%d)', r.status_code)
            return r.text
        elif template_url.startswith(local_prefix):
            fn = template_url[len(local_prefix):]
            return open(fn, 'r').read()
        else:
            # try local file
            fn = template_url
            return open(fn, 'r').read()
    except IOError as e:
        raise KeyError(e.strerror)
    except requests.ConnectionError as e:
        raise KeyError(e)


def getTemplateSummary(client, template_url):
    '''Returns template summary'''
    body = getTemplateBody(template_url)
    return client.get_template_summary(TemplateBody=body)
