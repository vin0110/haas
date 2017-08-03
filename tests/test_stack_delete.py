import unittest
import boto3
from haascli.haas import cli
from click.testing import CliRunner
from moto import mock_cloudformation
from utils import create_stack


class TestStackDelete(unittest.TestCase):
    '''
    '''
    def setUp(self):
        # create runner
        self.runner = CliRunner()
        mock = mock_cloudformation()
        mock.start()
        self.mock_client = boto3.client('cloudformation')

        # open template body
        f = open('tests/mock.json', 'r')
        self.template_body = f.read()
        f.close()

    def tearDown(self):
        pass

    @mock_cloudformation
    def test_delete(self):
        # first created these stacks in setUp, but didn't carry over
        # "create" two stacks
        create_stack('tank', 'never', self.template_body, self.mock_client)
        create_stack('beef', 'canoe', self.template_body, self.mock_client)

        # use incorrect name
        r = self.runner.invoke(cli, ['stack', 'delete', 'booty'])

        # check that both are still there
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertEqual(0, r.exit_code)
        statuses = r.output.strip().split('\n')
        self.assertEqual(2, len(statuses))
        self.assertTrue(statuses[0].startswith('tank'))
        self.assertTrue(statuses[1].startswith('beef'))

        # use correct name
        r = self.runner.invoke(cli, ['stack', 'delete', 'beef'])

        # check that both are still there
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertEqual(0, r.exit_code)
        statuses = r.output.strip().split('\n')
        self.assertEqual(1, len(statuses))
        self.assertTrue(statuses[0].startswith('tank'))

        # try it again
        r = self.runner.invoke(cli, ['stack', 'delete', 'beef'])

        # check that both are still there
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertEqual(0, r.exit_code)
        statuses = r.output.strip().split('\n')
        self.assertEqual(1, len(statuses))
        self.assertTrue(statuses[0].startswith('tank'))
        self.assertTrue('beef' not in r.output)

        # remove last one
        r = self.runner.invoke(cli, ['stack', 'delete', 'tank'])

        # check it
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertEqual(0, r.exit_code)
        statuses = r.output.strip().split('\n')
        self.assertTrue('tank' not in r.output)
