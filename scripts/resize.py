import sys
import os
import base64
import re
import fnmatch

from executor import execute


def lookup_node_ip():
    node_ip = execute("curl -s http://169.254.169.254/latest/meta-data/local-ipv4", capture=True)
    return node_ip


def lookup_dfs_files(esp_ip):
    cmd = "/opt/HPCCSystems/bin/dfuplus server={} action=list name=*"\
          .format(esp_ip)
    output = execute(cmd, capture=True)
    file_list = output.strip().split('\n')[1:]
    return file_list


def generate_distribute_ecl(logical_filename, esp_ip):
    exported_xml = "/tmp/{}.xml".format(logical_filename)
    cmd = "/opt/HPCCSystems/bin/dfuplus server={} action=savexml srcname={} dstxml={}".format(
        esp_ip, logical_filename, exported_xml)
    execute(cmd)

    target_cluster = execute('grep "group=" "{}"'.format(exported_xml), capture=True)
    # mythor or myroxie but we need thor or roxie
    target_cluster = target_cluster.split('=')[-1].replace('"', '').replace('my', '').strip()
    ecl_record = execute("sed -n '/<ECL/,/<\/ECL/p' {}".format(exported_xml), capture=True)
    ecl_record = ecl_record.replace('<ECL>', '').replace('</ECL>', '').replace('&#10;', '').strip()

    # @TODO: not sure the following path prefix ~ will be applicable to all cases?
    file_format = 'CSV'
    ecl_code = '''IMPORT STD;
layout := {ecl_record}

STD.File.RenameLogicalFile('~{logical_filename}', '~{logical_filename}.origin');
ds := DATASET('~{logical_filename}.origin', layout, {file_format});
OUTPUT(DISTRIBUTE(ds), ,'~{logical_filename}');
STD.File.DeleteLogicalFile('~{logical_filename}.origin');
'''.format(ecl_record=ecl_record, logical_filename=logical_filename, file_format=file_format)

    return ecl_code, target_cluster


def run_ecl(ecl_program, target_cluster, esp_ip, job_name='resize'):
    cmd = "/opt/HPCCSystems/bin/ecl run -v --server {} --target {} --name={} {}".format(
        esp_ip,
        target_cluster,
        job_name,
        ecl_program
    )
    return execute(cmd)


def resize_file(logical_filename, node_ip):
    ecl_code, target_cluster = generate_distribute_ecl(logical_filename, node_ip)
    ecl_program = os.path.join('/tmp', "{}.ecl".format(base64.b64encode(logical_filename.encode()).decode()))
    job_name = 'resize-{}'.format(logical_filename)

    with open(ecl_program, 'w') as f:
        f.write(ecl_code)

    print('logical filename:', logical_filename)
    print('job name:', job_name)
    print('target cluster:', target_cluster)
    print('ecl program:', ecl_program)
    run_ecl(ecl_program, target_cluster, node_ip, job_name=job_name)


def main(regex):
    node_ip = lookup_node_ip()

    pattern = re.compile(fnmatch.translate(regex))
    for logical_filename in lookup_dfs_files(node_ip):
        print(logical_filename)
        if not pattern.match(logical_filename):
            print("Skip {}".format(logical_filename))
            continue

        resize_file(logical_filename, node_ip)


if __name__ == '__main__':
    regex = '*'
    if len(sys.argv) == 2:
        regex = sys.argv[1]
    elif len(sys.argv) > 2:
        print('wrong arguments')
        exit(-1)

    main(regex)
