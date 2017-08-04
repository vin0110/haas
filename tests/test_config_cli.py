import os
import unittest
import shutil

from click.testing import CliRunner

from haascli.haas import cli


class TestConfigCLI(unittest.TestCase):
    '''
    '''

    _is_initialized = False

    def setUp(self):
        # create runner
        self.runner = CliRunner()
        self.haas_dir = "/tmp/.haas_configcli"

        if not TestConfigCLI._is_initialized:
            shutil.rmtree(self.haas_dir, ignore_errors=True)
            TestConfigCLI._is_initialized = True
            os.makedirs(self.haas_dir, exist_ok=False)

    def tearDown(self):
        pass

    def test_new_config(self):
        r = self.runner.invoke(cli, ["--config_dir", self.haas_dir, "config", "new", "test1"])
        self.assertEqual(r.exit_code, 0)
        r = self.runner.invoke(cli, ["--config_dir", self.haas_dir, "config", "new", "test1"])
        self.assertEqual(r.exit_code, 1)
        pass
