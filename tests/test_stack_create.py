import unittest
import boto3
from haascli.haas import cli
from click.testing import CliRunner
from moto import mock_cloudformation


GITHUB_CFT_URL = 'https://raw.githubusercontent.com/vin0110/haas/master/'\
    'templates/haas_cft.json'


class TestStackCreate(unittest.TestCase):
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
    def test_create_bad(self):
        # test missing stack_name
        r = self.runner.invoke(cli, ['stack', 'create'])
        self.assertEqual(2, r.exit_code)
        self.assertTrue('Missing argument "stack_name"' in r.output)

        # test missing configuration
        r = self.runner.invoke(cli, ['stack', 'create', 'foo'])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('must define template_url' in r.output)

        # set template_url to a URL
        # getting ERROR: Connection refused: GET https://raw...
        # which only happens in testing. but this tests the decision making
        r = self.runner.invoke(cli, ['stack', 'create', 'foo', '-p',
                                     'template_url=' + GITHUB_CFT_URL])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('Connection refused: GET' in r.output)

        # set template to local file
        r = self.runner.invoke(cli, ['stack', 'create', 'foo', '-p',
                                     'template_url=tests/mock.json'])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('Missing parameter KeyName' in r.output)

        # set template to local file
        r = self.runner.invoke(cli, ['stack', 'create', 'foo', '-p',
                                     'template_url=file:///tests/mock.json'])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('Missing parameter KeyName' in r.output)

        r = self.runner.invoke(cli, ['stack', 'create', 'foo', '-p',
                                     'template_url=file://tests/mock.json'])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('Missing parameter KeyName' in r.output)

    @mock_cloudformation
    def test_create_with_parameters(self):
        r = self.runner.invoke(cli, ['stack', 'create', 'tank', '-p',
                                     'template_url=file://tests/mock.json',
                                     '-p', 'KeyName=never'])
        # @@@ why this exit_code?
        self.assertEqual(-1, r.exit_code)

        # check
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertTrue('tank' in r.output)

    @mock_cloudformation
    def test_create_with_file(self):
        r = self.runner.invoke(cli, ['--config_dir', '.',
                                     'stack', 'create', 'tank', '-f',
                                     'tests/config.yaml'])
        # @@@ why this exit_code?
        self.assertEqual(-1, r.exit_code)

        # check
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertTrue('tank' in r.output)

    @mock_cloudformation
    def test_create_with_nonfile(self):
        r = self.runner.invoke(cli, ['stack', 'create', 'tank', '-f',
                                     'tests/config.yaml'])
        self.assertTrue('No such file or directory' in r.output)

        # check
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertTrue('tank' not in r.output)
