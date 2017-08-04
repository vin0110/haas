import os
import unittest
import boto3
from haascli.haas import cli
from click.testing import CliRunner
from moto import mock_cloudformation
from utils import create_stack
from haascli import ROOT_DIR


class TestStackEvents(unittest.TestCase):
    '''
    '''
    def setUp(self):
        # create runner
        self.runner = CliRunner()
        mock = mock_cloudformation()
        mock.start()
        self.mock_client = boto3.client('cloudformation')

        # open template body
        f = open(os.path.join(ROOT_DIR, 'tests', 'mock.json'), 'r')
        self.template_body = f.read()
        f.close()               # use explicit close to suppress moto warning

    def tearDown(self):
        pass

    @mock_cloudformation
    def test_events(self):
        create_stack('tank', 'never', self.template_body, self.mock_client)

        # use incorrect name
        r = self.runner.invoke(cli, ['stack', 'events', 'booty'])
        self.assertEqual(-1, r.exit_code)
        self.assertEqual(0, len(r.output))

        # @@@ moto: no implement of paginator
        # use correct name
        # r = self.runner.invoke(cli, ['stack', 'events', 'tank'])
        # self.assertEqual(0, r.exit_code)
        # self.assertEqual(2, len(r.output.strip().split('\n')))
