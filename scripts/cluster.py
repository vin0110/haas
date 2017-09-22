import sys

from utils import CommandAgent


def init(ips, thor_nodes, roxie_nodes, support_nodes, slaves_per_node):
    ip_list = ips.split(',')

    with CommandAgent(concurrency=len(ip_list)) as agent:
        for node_ip in ip_list:
            # the RemoteCommand does not work with the identity file well
            agent.submit_command("ssh -i /home/hpcc/.ssh/id_rsa {}".format(node_ip) +
                                 " -o StrictHostKeyChecking=no " +
                                 "bash /opt/haas/auto_hpcc.sh {} {} {} {}".format(
                                     thor_nodes, roxie_nodes, support_nodes, slaves_per_node),
                                 user='hpcc', sudo=True)


if __name__ == '__main__':
    op, thor_nodes, roxie_nodes, support_nodes, slaves_per_node, ips = sys.argv[1:]

    try:
        if op == 'init':
            init(ips, thor_nodes, roxie_nodes, support_nodes, slaves_per_node)
    except:
        sys.exit(-1)

    sys.exit(0)
