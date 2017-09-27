import sys
import os
import glob
import hashlib
import re
import fnmatch
import base64

from executor import execute

from utils import CommandAgent
from utils import ServiceController
# from utils import RedirectOutput

DFS_DIR = "/var/lib/HPCCSystems/hpcc-data"
DROPZONE_DIR = "/var/lib/HPCCSystems/mydropzone"


class HPCCTopology:
    @staticmethod
    def generate():
        output = execute("/opt/HPCCSystems/sbin/configgen -env "
                         "/etc/HPCCSystems/environment.xml -listall2",
                         silent=True, capture=True)
        topology = HPCCTopology.parse(output)
        return HPCCTopology(topology)

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
        return topology

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
    ip = execute("curl -s http://169.254.169.254/latest/meta-data/local-ipv4", capture=True)
    return ip


def lookup_dfs_files(esp_ip):
    cmd = "/opt/HPCCSystems/bin/dfuplus server={} action=list name=*"\
          .format(esp_ip)
    output = execute(cmd, capture=True)
    file_list = output.strip().split('\n')[1:]
    return file_list


def lookup_workunits(daliserver_ip):
    cmd = "/opt/HPCCSystems/bin/wutool DALISERVER={} list"\
          .format(daliserver_ip)
    output = execute(cmd, capture=True)
    wu_list = [line.split(' ')[0] for line in output.strip().splitlines()]
    return wu_list


def lookup_node_index(node_ip, node_ip_list):
    if node_ip in node_ip_list:
        slave_index = node_ip_list.index(node_ip) + 1
    else:
        slave_index = -1
    return slave_index


def generate_hash(data, prefix='-'):
    hash_prefix = hashlib.md5(data.encode('utf-8')).hexdigest()
    return hash_prefix + prefix + data


def workunit(op, bucket, checkpoint, regex):
    topology = HPCCTopology.generate()
    daliserver_ip = topology.get_daliserver_list()[0]
    if lookup_private_ip() != daliserver_ip:
        print('This is not a DaliServer node. Aborted.')
        exit(-1)

    # @TODO: should we use shorter prefex?
    output_name = generate_hash("{}-workunits.tar.gz".format(checkpoint))
    output_dir = os.path.join('/tmp', checkpoint)
    execute("mkdir -p {}".format(output_dir))
    output_path = os.path.join(output_dir, output_name)

    workspace_dir = os.path.join(output_dir, 'workunits')
    execute("mkdir -p {}".format(workspace_dir))

    pattern = re.compile(fnmatch.translate(regex))
    if op == 'save':
        # @TODO: need to support regular expression
        wu_list = lookup_workunits(daliserver_ip)
        for wu in wu_list:
            if not pattern.match(wu):
                print('Skip {}'.format(wu))
                continue
            # include the *.so files
            print("Exporting {}".format(wu))
            execute("/opt/HPCCSystems/bin/wutool DALISERVER={} archive {} "
                    "TO={} INCLUDEFILES=1".format(
                        daliserver_ip, wu, workspace_dir))
        print("Creating {} from {}".format(output_path, workspace_dir))
        execute("tar zcf {} -C {} .".format(output_path, workspace_dir))
        print("Created {}".format(output_path))
        print("Coping {} to s3 at {}".format(output_path, bucket))
        execute("aws s3 cp {} s3://{}".format(output_path, bucket))
        print("Copied {}".format(output_path))
        execute("rm {}".format(output_path))
    elif op == 'restore':
        print("Coping {} from s3://{}/{}".format(output_path, bucket,
                                                 output_name))
        execute("aws s3 cp s3://{}/{} {}".format(bucket, output_name,
                                                 output_path))
        print("Copied {}".format(output_path))
        print("Extracting {} to {}".format(output_path, workspace_dir))
        execute("tar zxf {} -C {} --no-overwrite-dir"
                .format(output_path, workspace_dir))
        print("Extracted {}".format(output_path))
        for f in glob.glob(os.path.join(workspace_dir, '*.xml')):
            print("Importing {}".format(f))
            # change the ip address of the .DLL/.so file
            ip_match = "(\\b[0-9]{1,3}\.){3}[0-9]{1,3}\\b"
            cmd_replace = 'sed -i -r \'s/location="\/\/{}\//'\
                          'location="\/\/{}\//\' {}'\
                          .format(ip_match, daliserver_ip, f)
            execute(cmd_replace)
            # @TODO: need to sudo or use hpcc as the user?
            execute("sudo /opt/HPCCSystems/bin/wutool DALISERVER={} "
                    "restore {} INCLUDEFILES=1".format(daliserver_ip, f))
        execute("rm {}".format(output_path))


def dropzone(op, bucket, checkpoint, regex):
    # TODO: now supports only the dropzone on the esp node
    topology = HPCCTopology.generate()
    esp_ip = topology.get_esp_list()[0]
    if lookup_private_ip() != esp_ip:
        print('This is not the ESP node. Aborted.')
        return -1

    output_name = generate_hash("{}-dropzone.tar.gz".format(checkpoint))
    output_dir = os.path.join('/tmp', checkpoint)
    execute("mkdir -p {}".format(output_dir))
    output_path = os.path.join(output_dir, output_name)

    if op == 'save':
        print("Creating {} from {}".format(output_path, DROPZONE_DIR))
        # support both regular files and symbolic links
        cmd = "cd {}; find . -type f -or -type l -name '{}' | tar zcf {} -C . --dereference --files-from -".format(
            DROPZONE_DIR, regex, output_path)
        execute("echo {} | base64 -d | bash".format(base64.b64encode(cmd.encode()).decode()))
        print("Created {}".format(output_path))
        # it uses multiparts uploadby default
        # http://docs.aws.amazon.com/cli/latest/userguide/using-s3-commands.html
        # @TODO: should we use sync instead of cp?
        print("Copying {} to s3 at {}".format(output_path, bucket))
        execute("aws s3 cp {} s3://{}".format(output_path, bucket))
        print("Copied {}".format(output_path))
        execute("rm {}".format(output_path))
    elif op == 'restore':
        print("Copying {} from s3://{}/{}".format(output_path, bucket,
                                                  output_name))
        execute("aws s3 cp s3://{}/{} {}".format(bucket, output_name,
                                                 output_path))
        print("Copied {}".format(output_path))
        print("Extracting {} to {}".format(output_path, DROPZONE_DIR))
        execute("tar zxf {} -C {} --no-overwrite-dir".format(output_path,
                                                             DROPZONE_DIR))
        print("Extracted {}".format(output_path))
        execute("rm {}".format(output_path))
    return 0


def dfs(op, bucket, checkpoint, regex):
    topology = HPCCTopology.generate()
    node_ip = lookup_private_ip()
    node_list = topology.get_node_list()
    if node_ip not in node_list:
        print("This node is neither a Thor nor Roxie node")
        exit(-1)

    node_index = node_list.index(node_ip) + 1

    output_name = generate_hash("{}-files{}.tar.gz".format(
        checkpoint, node_index))
    output_dir = os.path.join('/tmp', checkpoint)
    execute('mkdir -p {}'.format(output_dir))
    output_path = os.path.join(output_dir, output_name)

    # filter out
    if op == 'save':
        print("Creating {} from {}".format(output_path, DFS_DIR))
        # list only files but not directories
        cmd = "cd {}; find . -type f -name '{}' | tar zcf {} -C . --files-from -".format(DFS_DIR, regex, output_path)
        execute("echo {} | base64 -d | bash".format(base64.b64encode(cmd.encode()).decode()))
        #execute("cd {}; find . -type f -name '{}' | tar zcf {} -C . --files-from -"
        #        .format(DFS_DIR, regex, output_path))
        print("Created {}".format(output_path))
        print("Copying {} to s3 at {}".format(output_path, bucket))
        execute("aws s3 cp {} s3://{}".format(output_path, bucket))
        print("Copied {}".format(output_path))
    elif op == 'restore':
        print("Copying {} from s3://{}/{}".format(output_path, bucket,
                                                  output_name))
        execute("aws s3 cp s3://{}/{} {}".format(bucket, output_name,
                                                 output_path))
        print("Copied {}".format(output_path))
        # @TODO: the original user attributes are kept
        execute("mkdir -p {}".format(DFS_DIR))
        print("Extracting {} to {}".format(output_path, DFS_DIR))
        execute("tar zxf {} -C {} --no-overwrite-dir".format(output_path,
                                                                  DFS_DIR))
        print("Extracted {}".format(output_path))


def dali_metadata(op, bucket, checkpoint, regex):
    topology = HPCCTopology.generate()
    node_ip = lookup_private_ip()
    if node_ip != topology.get_esp_list()[0]:
        print("This node is not an ESP node")
        exit(-1)

    output_name = generate_hash("{}-dali.tar.gz".format(checkpoint))
    output_path = os.path.join('/tmp', checkpoint, output_name)

    workspace_dir = os.path.join('/tmp', checkpoint, 'dali_metadata')
    execute("mkdir -p {}".format(workspace_dir))

    pattern = re.compile(fnmatch.translate(regex))
    if op == 'save':
        dfs_file_list = lookup_dfs_files(node_ip)
        for f in dfs_file_list:
            if not pattern.match(f):
                print("Skip {}".format(f))
                continue
            print("Exporting {}".format(f))
            # @TODO: need to regular expression
            cmd_export = "/opt/HPCCSystems/bin/dfuplus server={} "\
                         "action=savexml srcname={} dstxml={}/{}.xml".format(
                             node_ip, f, workspace_dir, f)
            execute(cmd_export)
        print("Creating {} from {}".format(output_path, workspace_dir))
        execute("tar zcf {} -C {} .".format(output_path, workspace_dir))
        print("Created {}".format(output_path))
        print("Copying {} to s3 at {}".format(output_path, bucket))
        execute("aws s3 cp {} s3://{}".format(output_path, bucket))
        print("Copied {}".format(output_path))
    elif op == 'restore':
        print("Copying {} from s3://{}/{}".format(output_path,
                                                  bucket, output_name))
        execute("aws s3 cp s3://{}/{} {}".format(bucket, output_name,
                                                 output_path))
        print("Copied {}".format(output_path))
        print("Extracting {} to {}".format(output_path, workspace_dir))
        execute("tar zxf {} -C {} --no-overwrite-dir".format(output_path,
                                                             workspace_dir))
        print("Extracted {}".format(output_path))

        node_ip_list = topology.get_node_list()
        replaced_group_text = ",".join(node_ip_list)
        for f in [f for f in os.listdir(workspace_dir) if f.endswith('.xml')]:
            if not pattern.match(f):
                print("Skip {}".format(f))
                continue
            xml_path = os.path.join(workspace_dir, f)
            print("Importing {}".format(xml_path))
            cmd_replace = "sed -i 's/<Group>.*<\/Group>/<Group>{}<\/Group>/' "\
                          "{}".format(replaced_group_text, xml_path)
            execute(cmd_replace)
            logical_filename = ".".join(f.split("/")[-1].split('.')[:-1])
            cmd_import = "/opt/HPCCSystems/bin/dfuplus server={} "\
                         "action=add srcxml={} dstname={}".format(
                             node_ip, xml_path, logical_filename)
            execute(cmd_import)


class CheckpointService:
    service_lock = '/tmp/.haas_checkpoint.lock'
    service_output = '/tmp/haas_checkpoint.out'

    @staticmethod
    def is_available():
        # return false if CheckpointService is running
        return execute("flock -n {} date".format(
            CheckpointService.service_lock), check=False, silent=True)

    @staticmethod
    def run(cmd, stdout=None, stderr=None):
        print('Running the checkpoint service: {}'.format(cmd))
        execute('flock -n {} -c "{}"'.format(
            CheckpointService.service_lock,
            cmd,
            stdout_file=CheckpointService.service_output if stdout is None
            else stdout,
            stderr_file=CheckpointService.service_output if stderr is None
            else stderr,
            check=True, silent=False)
        )


def available():
    if CheckpointService.is_available():
        return exit(0)
    else:
        return exit(1)


def service_workunit(op, bucket, checkpoint, regex):
    try:
        print("Workunit service is running")
        return workunit(op, bucket, checkpoint, regex)
    except Exception:
        import traceback
        traceback.print_exc()
        print('Failed to run the workunit service')
        exit(1)


def service_dropzone(op, bucket, checkpoint, regex):
    if CheckpointService.is_available():
        print("Dropzone service is running")
        return dropzone(op, bucket, checkpoint, regex)
    else:
        print('Failed to run the dropzone service')
        return -1


def service_dfs(op, bucket, checkpoint, regex):
    if not CheckpointService.is_available():
        print("CheckpointService is still running")
        exit(1)

    topology = HPCCTopology.generate()
    node_list = topology.get_node_list()
    print(node_list)

    print("CheckpointService is performing the {} operation on the dfs "
          "component".format(op))

    controller = ServiceController('dfs')
    with CommandAgent(concurrency=len(node_list)) as agent:
        for node_ip in node_list:
            cmd = "python3 /opt/haas/checkpoint.py slave_dfs {} {} {} '{}'".format(
                                     op, bucket, checkpoint, regex)
            print(cmd)
            agent.submit_command("ssh -i /home/hpcc/.ssh/id_rsa {}".format(node_ip) +
                                 " -o StrictHostKeyChecking=no" +
                                 " 'echo {} | base64 -d | bash'".format(base64.b64encode(cmd.encode()).decode()),
                                 user='hpcc', sudo=True,
                                 stdout_file=open(controller.get_output_path(), 'w'),
                                 stderr_file=open(controller.get_output_path(), 'w')
                                 )
    # with open(controller.get_output_path(), 'w') as f:
    #   with RedirectOutput(f, f):
    #        dali_metadata(op, bucket, checkpoint, regex)
    exit(0)


def main():
    # always has 5 arguments:
    # 1: what dfs|wu|dz
    # 2: op: save|restore
    # 3: bucket
    # 4: checkpoint name
    # 5: regex

    if len(sys.argv) != 6:
        exit(-1)

    what, op, bucket, checkpoint, regex = sys.argv[1:]

    try:
        assert what in ['dfs', 'wu', 'dz', 'slave_dfs']
        assert op in ['save', 'restore']
    except AssertionError:
        exit(-1)

    if what == 'dfs':
        service_dfs(op, bucket, checkpoint, regex)
    elif what == 'wu':
        service_workunit(op, bucket, checkpoint, regex)
    elif what == 'dz':
        service_dropzone(op, bucket, checkpoint, regex)
    elif what == 'slave_dfs':
        dfs(op, bucket, checkpoint, regex)
    else:
        # cannot get here; exit anyway
        exit(-1)


if __name__ == '__main__':
    main()
