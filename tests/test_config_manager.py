import os
import logging
import unittest
import shutil

import haascli
from haascli.config import HaaSConfiguration, HaasConfigurationKey, HaasConfigurationManager


class TestConfigurationManager(unittest.TestCase):
    '''
    '''

    _is_initialized = False

    def setUp(self):
        # haascli.setup_logging(level=logging.DEBUG)
        self.haas_dir = "/tmp/.haas_configmanager"
        if not TestConfigurationManager._is_initialized:
            shutil.rmtree(self.haas_dir, ignore_errors=True)
            TestConfigurationManager._is_initialized = True
        self.config_manager = HaasConfigurationManager(haas_dir=self.haas_dir)
        self.haas_config = HaaSConfiguration(
            {
                HaasConfigurationKey.AWS_ACCESS_KEY_ID: 'key1',
                HaasConfigurationKey.AWS_SECRET_ACCESS_KEY_ID: 'secret1'
            }
        )

    def tearDown(self):
        pass

    def test_singleton_manager(self):
        m1 = HaasConfigurationManager()
        m2 = HaasConfigurationManager()
        self.assertTrue(m1 == m2)

    def test_add_config(self):
        config_name = 'test_add'
        self.config_manager.add(
            config_name,
            HaaSConfiguration(
                {
                    HaasConfigurationKey.AWS_ACCESS_KEY_ID: 'key1',
                    HaasConfigurationKey.AWS_SECRET_ACCESS_KEY_ID: 'secret1'
                }
            )
        )
        self.assertTrue(self.config_manager.exists(config_name))

    def test_manager_reload(self):
        config_name = 'test_reload'
        config_path = self.config_manager.get_config_path(config_name)
        self.haas_config.to_file(config_path)
        self.config_manager.reload()
        self.assertTrue(self.config_manager.exists(config_name))

    def test_config_key(self):
        self.assertEqual(self.haas_config.get(HaasConfigurationKey.AWS_SECRET_ACCESS_KEY_ID), 'secret1')
        with self.assertRaises(Exception):
            self.haas_config.get("testkey1")

    def test_config_dump(self):
        config_path = "/tmp/test.yaml"
        HaaSConfiguration.dump(self.haas_config, config_path)
        self.assertTrue(os.path.exists(config_path))

    def test_config_load(self):
        config_path = "/tmp/test.yaml"
        HaaSConfiguration.dump(self.haas_config, config_path)
        self.assertTrue(os.path.exists(config_path))
        haas_config = HaaSConfiguration.load(config_path)
        self.assertTrue(haas_config.get(HaasConfigurationKey.AWS_ACCESS_KEY_ID) == 'key1')
