import os
import logging
import glob
import hashlib
import copy

import click
from executor import execute
from executor.ssh.client import RemoteCommand
import netifaces as ni

from haascli.utils import CommandAgent


logger = logging.getLogger(__name__)


class HPCCTopology:
    @staticmethod
    def generate():
        output = execute("/opt/HPCCSystems/sbin/configgen -env /etc/HPCCSystems/environment.xml -listall2",
                      silent=True, capture=True)
        return HPCCTopology.parse(output)

    @staticmethod
    def parse(output):
        topology = {
            'ThorMaster': None,
            'ThorSlave': [],
            'RoxieServer': [],
            'Dafilesrv': [],
            'DaliServer': [],
            'DfuServer': [],
            'Esp': [],
            'EclCCServer': [],
            'EclAgent': [],
            'SashaServer': [],
            'FTSlave': [],
            'EclScheduler': [],
        }
        for line in output.strip().splitlines():
            process_name, component, ip, _, component_dir, _ = line.split(',')
            if 'ThorMaster' in process_name:
                topology['ThorMaster'] = ip
            else:
                topology[process_name.replace('Process', '')].append(ip)
        return HPCCTopology(topology)

    def __init__(self, topology):
        self.topology = topology

    def get_thor_master(self):
        return self.topology['ThorMaster']

    def get_thor_slaves(self):
        return self.topology['ThorSlave']

    def get_roxie_servers(self):
        return self.topology['RoxieServer']

    def get_esp_list(self):
        return self.topology['Esp']

    def get_daliserver_list(self):
        return self.topology['DaliServer']

    def get_node_list(self):
        node_list = self.get_thor_slaves()
        for roxie_node in self.get_roxie_servers():
            if roxie_node not in node_list:
                node_list.append(roxie_node)
        return node_list


def lookup_private_ip():
    # workaround for VCL and AWS, maybe
    interface_list = ni.interfaces()
    selected_interface = 'eth0'
    for interface in interface_list:
        if '0' in interface:
            selected_interface = interface
            break
    ni.ifaddresses(selected_interface)
    ip = ni.ifaddresses(selected_interface)[2][0]['addr']
    return ip


def lookup_dfs_files(esp_ip):
    cmd = "/opt/HPCCSystems/bin/dfuplus server={} action=list name=*".format(esp_ip)
    output = execute(cmd, capture=True)
    file_list = output.strip().split('\n')[1:]
    return file_list


def lookup_workunits(daliserver_ip):
    cmd = "/opt/HPCCSystems/bin/wutool DALISERVER={} list".format(daliserver_ip)
    output = execute(cmd, capture=True)
    wu_list = [line.split(' ')[0] for line in output.strip().splitlines()]
    return wu_list


def lookup_node_index(node_ip, node_ip_list):
    slave_index = node_ip_list.index(node_ip) + 1 if node_ip in node_ip_list else -1
    return slave_index


def generate_hash(data, prefix='-'):
    hash_prefix = hashlib.md5(data.encode('utf-8')).hexdigest()
    return hash_prefix + prefix + data


@click.group()
@click.option('--name', default='mycheckpoint', help='The checkpoint name')
@click.option('--s3_bucket', default='hpcc_checkpoint')
@click.option('--user', default='hpcc')
@click.pass_context
def cli(ctx, **kwargs):
    ctx.obj = kwargs
    ctx.obj['hpcc_config'] = "/etc/HPCCSystems/environment.xml"
    ctx.obj['hpcc_system_dir'] = "/opt/HPCCSystems"
    ctx.obj['dropzone_dir'] = "/var/lib/HPCCSystems/mydropzone"
    # @TODO: needs to load path from environment.xml; multiple paths are possible
    ctx.obj['dfs_dir'] = "/var/lib/HPCCSystems/hpcc-data"
    ctx.obj['tmp_dir'] = os.path.join("/tmp", ctx.obj['name'])
    execute("mkdir -p {}".format(ctx.obj['tmp_dir']))

    # @TODO: should we initialize first?
    execute("aws s3 mb s3://{}".format(ctx.obj['s3_bucket']), silent=True)


@cli.command()
@click.argument('op', type=click.Choice(['save', 'restore']))
@click.pass_context
def workunit(ctx, op):
    topology = HPCCTopology.generate()
    daliserver_ip = topology.get_daliserver_list()[0]
    if lookup_private_ip() != daliserver_ip:
        print('This is not a DaliServer node. Aborted.')
        ctx.abort()

    # @TODO: should we use shorter prefex?
    output_name = generate_hash("{}-workunits.tar.gz".format(ctx.obj['name']))
    output_path = os.path.join(ctx.obj['tmp_dir'], output_name)

    workspace_dir = os.path.join(ctx.obj['tmp_dir'], 'workunits')
    execute("mkdir -p {}".format(workspace_dir))

    if op == 'save':
        # @TODO: need to support regular expression
        wu_list = lookup_workunits(daliserver_ip)
        for wu in wu_list:
            # include the *.so files
            execute("/opt/HPCCSystems/bin/wutool DALISERVER={} archive {} TO={} INCLUDEFILES=1".format(
                daliserver_ip, wu, workspace_dir)
            )
        execute("tar zcvf {} -C {} .".format(output_path, workspace_dir))
        execute("aws s3 cp {} s3://{}".format(output_path, ctx.obj['s3_bucket']))
    elif op == 'restore':
        execute("aws s3 cp s3://{}/{} {}".format(ctx.obj['s3_bucket'], output_name, output_path))
        execute("tar zxvf {} -C {} --no-overwrite-dir".format(output_path, workspace_dir))
        for f in glob.glob(os.path.join(workspace_dir, '*.xml')):
            # @TODO: need to sudo or use hpcc as the user
            execute("sudo /opt/HPCCSystems/bin/wutool DALISERVER={} restore {} INCLUDEFILES=1".format(daliserver_ip, f))


@cli.command()
@click.argument('op', type=click.Choice(['save', 'restore']))
@click.pass_context
def dropzone(ctx, op):
    # TODO: now supports only the dropzone on the esp node
    topology = HPCCTopology.generate()
    esp_ip = topology.get_esp_list()[0]
    if lookup_private_ip() != esp_ip:
        print('This is not the ESP node. Aborted.')
        ctx.abort()

    output_name = generate_hash("{}-dropzone.tar.gz".format(ctx.obj['name']))
    output_path = os.path.join(ctx.obj['tmp_dir'], output_name)

    if op == 'save':
        execute("tar zcvf {} -C {} .".format(output_path, ctx.obj['dropzone_dir']))
        # it uses multiparts uploadby default
        # http://docs.aws.amazon.com/cli/latest/userguide/using-s3-commands.html
        execute("aws s3 cp {} s3://{}".format(output_path, ctx.obj['s3_bucket']))
    elif op == 'restore':
        execute("aws s3 cp s3://{}/{} {}".format(ctx.obj['s3_bucket'], output_name, output_path))
        execute("tar zxvf {} -C {} --no-overwrite-dir".format(output_path, ctx.obj['dropzone_dir']))


@cli.command()
@click.argument('op', type=click.Choice(['save', 'restore']))
@click.option('--filter', default='.*', help='The regular expression for filtering the file path')
@click.pass_context
def dfs(ctx, op, filter):
    topology = HPCCTopology.generate()
    node_ip = lookup_private_ip()
    node_list = topology.get_node_list()
    if node_ip not in node_list:
        print("This node is nither a Thor nor Roxie node")
        ctx.abort()

    node_index = node_list.index(node_ip) + 1

    output_name = generate_hash("{}-files{}.tar.gz".format(ctx.obj['name'], node_index))
    output_path = os.path.join(ctx.obj['tmp_dir'], output_name)

    # filter out
    if op == 'save':
        execute("tar zcvf {} -C {} .".format(output_path, ctx.obj['dfs_dir']))
        execute("aws s3 cp {} s3://{}".format(output_path, ctx.obj['s3_bucket']))
    elif op == 'restore':
        execute("aws s3 cp s3://{}/{} {}".format(ctx.obj['s3_bucket'], output_name, output_path))
        # @TODO: the original user attributes are kept
        execute("sudo tar zxvf {} -C {} --no-overwrite-dir".format(output_path, ctx.obj['dfs_dir']))


@cli.command()
@click.argument('op', type=click.Choice(['save', 'restore']))
@click.option('--filter', default='.*', help='The regular expression for filtering the file path')
@click.pass_context
def dali_metadata(ctx, op, filter):
    topology = HPCCTopology.generate()
    node_ip = lookup_private_ip()
    if node_ip != topology.get_esp_list()[0]:
        print("This node is not an ESP node")
        ctx.abort()

    output_name = generate_hash("{}-dali.tar.gz".format(ctx.obj['name']))
    output_path = os.path.join(ctx.obj['tmp_dir'], output_name)

    workspace_dir = os.path.join(ctx.obj['tmp_dir'], 'dali_metadata')
    execute("mkdir -p {}".format(workspace_dir))

    if op == 'save':
        dfs_file_list = lookup_dfs_files(node_ip)
        for f in dfs_file_list:
            # @TODO: need to regular expression
            cmd_export = "/opt/HPCCSystems/bin/dfuplus server={} action=savexml srcname={} dstxml={}/{}.xml".format(
                node_ip, f, workspace_dir, f)
            execute(cmd_export)
        execute("tar zcvf {} -C {} .".format(output_path, workspace_dir))
        execute("aws s3 cp {} s3://{}".format(output_path, ctx.obj['s3_bucket']))
    elif op == 'restore':
        execute("aws s3 cp s3://{}/{} {}".format(ctx.obj['s3_bucket'], output_name, output_path))
        execute("tar zxvf {} -C {} --no-overwrite-dir".format(output_path, workspace_dir))

        node_ip_list = ctx.invoke(topology.get_node_list)
        replaced_group_text = ",".join(node_ip_list)
        for f in [f for f in os.listdir(workspace_dir) if f.endswith('.xml')]:
            xml_path = os.path.join(workspace_dir, f)
            print("Processing {}".format(xml_path))
            cmd_replace = "sed -i 's/<Group>.*<\/Group>/<Group>{}<\/Group>/' {}".format(replaced_group_text, xml_path)
            execute(cmd_replace)
            logical_filename = ".".join(f.split("/")[-1].split('.')[:-1])
            cmd_import = "/opt/HPCCSystems/bin/dfuplus server={} action=add srcxml={} dstname={}".format(
                node_ip, xml_path, logical_filename)
            execute(cmd_import)


class CheckpointService:
    service_lock = '/tmp/.haas_checkpoint.lock'

    @staticmethod
    def is_available():
        return not os.path.exists(CheckpointService.service_lock)

    @staticmethod
    def run(cmd):
        execute("echo '{}' > {}".format(cmd, CheckpointService.service_lock))

@cli.command()
@click.argument('op', type=click.Choice(['save', 'restore']))
@click.pass_context
def service_workunit(ctx):
    pass