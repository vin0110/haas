import unittest

from click.testing import CliRunner

from haascli.haas import cli
from haascli.checkpoint import HPCCTopology


class TestCheckpoint(unittest.TestCase):
    '''
    '''

    _is_initialized = False

    def setUp(self):
        # create runner
        self.runner = CliRunner()
        self.output = '''
EclAgentProcess,myeclagent,10.25.2.168,,/var/lib/HPCCSystems/myeclagent,
FTSlaveProcess,myftslave,10.25.2.168,,/var/lib/HPCCSystems/myftslave,
FTSlaveProcess,myftslave,10.25.2.167,,/var/lib/HPCCSystems/myftslave,
FTSlaveProcess,myftslave,10.25.2.165,,/var/lib/HPCCSystems/myftslave,
SashaServerProcess,mysasha,10.25.2.168,8877,/var/lib/HPCCSystems/mysasha,.
RoxieServerProcess,myroxie,10.25.2.167,,/var/lib/HPCCSystems/myroxie,
RoxieServerProcess,myroxie,10.25.2.165,,/var/lib/HPCCSystems/myroxie,
DaliServerProcess,mydali,10.25.2.168,7070,/var/lib/HPCCSystems/mydali,
DfuServerProcess,mydfuserver,10.25.2.168,,/var/lib/HPCCSystems/mydfuserver,
EclCCServerProcess,myeclccserver,10.25.2.168,,/var/lib/HPCCSystems/myeclccserver,
EspProcess,myesp,10.25.2.168,,/var/lib/HPCCSystems/myesp,
DafilesrvProcess,mydafilesrv,10.25.2.168,,/var/lib/HPCCSystems/mydafilesrv,
DafilesrvProcess,mydafilesrv,10.25.2.167,,/var/lib/HPCCSystems/mydafilesrv,
DafilesrvProcess,mydafilesrv,10.25.2.165,,/var/lib/HPCCSystems/mydafilesrv,
ThorMasterProcess,mythor,10.25.2.168,20000,/var/lib/HPCCSystems/mythor,
ThorSlaveProcess,mythor,10.25.2.165,,/var/lib/HPCCSystems/mythor,
ThorSlaveProcess,mythor,10.25.2.167,,/var/lib/HPCCSystems/mythor,
EclSchedulerProcess,myeclscheduler,10.25.2.168,,/var/lib/HPCCSystems/myeclscheduler,
        '''
        self.dfs_files = [
            '.::wimbledon-men-2013.csv',
            'tutorial::yn::originalperson',
            'tutorial::yn::tutorialperson'
        ]

    def tearDown(self):
        pass

    def test_hpcc_topology_parse(self):
        topology = HPCCTopology.parse(self.output)
        assert topology.get_thor_master() == '10.25.2.168'
        assert sorted(topology.get_thor_slaves()) == sorted(['10.25.2.165', '10.25.2.167'])
        assert sorted(topology.get_roxie_servers()) == sorted(['10.25.2.165', '10.25.2.167'])
        assert sorted(topology.get_esp_list()) == sorted(['10.25.2.168'])

    def test_dfs_filter(self):
        pass
