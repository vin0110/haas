import logging

from executor.concurrent import CommandPool
from executor.ssh.client import RemoteCommand
from executor import ExternalCommand


class Node(object):
    def __init__(self, hostname, ip):
        self.hostname = hostname
        self.ip = ip

    def get_hostname(self):
        return self.hostname

    def get_ip(self):
        return self.ip

    def __eq__(self, other):

        return isinstance(other, self.__class__) and self.ip == other.ip

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "%s(%s)" % (self.hostname, self.ip)

    def __hash__(self):
        return hash(self.__repr__())


class CommandAgent:

    def __init__(self, concurrency=8, show_result=False):
        self.pool = CommandPool(concurrency=concurrency)
        self.cmd_records = {}
        self.show_result = show_result
        self.logger = logging.getLogger('.'.join([__name__, self.__class__.__name__]))

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.pool.run()
        if not self.show_result:
            return
        i = 0
        for (identifier, cmd) in self.cmd_records.items():
            i = i + 1
            self.logger.debug("[{}] {}".format(i, cmd.ssh_alias if type(cmd) is RemoteCommand else identifier))
            self.logger.debug(cmd.output)

    def submit(self, cmd_id, cmd, *args, **kwargs):
        ec = None
        if type(cmd) is ExternalCommand or type(cmd) is RemoteCommand:
            ec = cmd
        else:
            ec = ExternalCommand(cmd, *args, **kwargs)
        ec.async = True
        self.cmd_records[cmd_id] = ec
        self.pool.add(ec)

    def submit_command(self, cmd, *args, **kwargs):
        self.submit(hash(cmd), ExternalCommand(cmd, *args, **kwargs))

    def submit_remote_command(self, host, cmd, *args, cid=None, **kwargs):
        if 'strict_host_key_checking' not in kwargs:
            kwargs['strict_host_key_checking'] = False
        if 'ignore_known_hosts' not in kwargs:
            kwargs['ignore_known_hosts'] = True
        host_used = host if isinstance(host, str) else host.get_ip() if isinstance(host, Node) else None
        if host_used is None:
            raise Exception("unknown host type: {}".format(type(host)))

        if cid is None:
            self.submit(hash(host_used + cmd), RemoteCommand(host_used, cmd, *args, **kwargs))
        else:
            self.submit(cid, RemoteCommand(host_used, cmd, *args, **kwargs))

    def submit_remote_commands(self, nodes, cmd, *args, cids=None, **kwargs):
        if cids is not None:
            for node, cid in zip(nodes, cids):
                self.submit_remote_command(node, cmd, *args, cid=cid, **kwargs)
        else:
            for node in nodes:
                self.submit_remote_command(node, cmd, *args, **kwargs)