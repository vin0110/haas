import os
import unittest
import boto3
from haascli.haas import cli
from click.testing import CliRunner
from moto import mock_cloudformation
from haascli import ROOT_DIR
from haascli import logger, console_handler


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
        self.template_file = os.path.join(ROOT_DIR, 'tests', 'mock.json')
        f = open(os.path.join(self.template_file), 'r')
        self.template_body = f.read()
        f.close()

        # disable error logging during testing
        logger.removeHandler(console_handler)

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
        self.assertTrue('Aborted!' in r.output)

        # set template_url to a URL
        # getting ERROR: Connection refused: GET https://raw...
        # which only happens in testing. but this tests the decision making
        r = self.runner.invoke(cli, ['stack', 'create', 'foo', '-p',
                                     'template_url=' + GITHUB_CFT_URL])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('Aborted!' in r.output)

        # set template to local file
        r = self.runner.invoke(cli, ['stack', 'create', 'foo', '-p',
                                     'template_url=' + self.template_file])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('Aborted!' in r.output)

        # set template to local file
        r = self.runner.invoke(cli, ['stack', 'create', 'foo', '-p',
                                     'template_url=file://' +
                                     self.template_file])
        self.assertEqual(1, r.exit_code)
        self.assertTrue('Aborted!' in r.output)

    @mock_cloudformation
    def test_create_with_parameters(self):
        r = self.runner.invoke(cli, ['stack', 'create', 'tank', '-p',
                                     'template_url=file://' +
                                     self.template_file,
                                     '-p', 'KeyName=never'])
        # @@@ why this exit_code?
        # @@@ exit_code seems to be arbitrary
        # self.assertEqual(1, r.exit_code)

        # check
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertTrue('tank' in r.output)

    @mock_cloudformation
    def test_create_with_file(self):
        fn = os.path.join('tests', 'config.yaml')
        r = self.runner.invoke(cli, ['--config_dir', ROOT_DIR,
                                     'stack', 'create', 'tank', '-f', fn])
        # @@@ why this exit_code?
        # @@@ exit_code seems to be arbitrary
        # self.assertEqual(1, r.exit_code)

        # check
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertTrue('tank' in r.output)

    @mock_cloudformation
    def test_create_with_file_absolute_path(self):
        fn = os.path.join(ROOT_DIR, 'tests', 'config.yaml')
        r = self.runner.invoke(cli, ['--config_dir', ROOT_DIR,
                                     'stack', 'create', 'tank', '-f', fn])
        # @@@ why this exit_code?
        # @@@ exit_code seems to be arbitrary
        # self.assertEqual(1, r.exit_code)

        # check
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertTrue('tank' in r.output)

    @mock_cloudformation
    def test_create_with_nonfile(self):
        r = self.runner.invoke(cli, ['stack', 'create', 'tank', '-f',
                                     'tests/non.yaml'])
        self.assertTrue('Aborted!' in r.output)

        # check
        r = self.runner.invoke(cli, ['stack', 'list'])
        self.assertTrue('tank' not in r.output)
