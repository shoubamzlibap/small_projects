# test_config_parser.py
# tests for config_parser.py

import os
import unittest
import yaml
from .. import config_parser

class testConfigParser(unittest.TestCase):

    @classmethod
    def setUp(self):
        """Create a config file used for parsing"""
        self.config_file = '/tmp/test_config.yml'
        config = {
            'animal': 'cat',
            'location': '/tmp/foobar.txt',
            'values': ['a', 'b', 'c', 23],
            }
        with open(self.config_file, 'w') as filehandle:
            filehandle.write(yaml.dump(config, default_flow_style=False,))

    @classmethod
    def tearDown(self):
        """Delete test config file"""
        os.unlink(self.config_file)

    def test_configParser_basic(self):
        """Basic interface test"""
        config = config_parser.configParser(self.config_file)
        self.assertEqual(config.config['animal'], 'cat')
        self.assertEqual(config.animal, 'cat')
        self.assertListEqual(config.values, ['a', 'b', 'c', 23])

    def test_configParser_default(self):
        """Setting defaults"""
        config = config_parser.configParser(
            self.config_file,
            defaults = {'foobar': 'barfoo', 'animal': 'dog'}
        )
        # defaults do not overwrite the provided values
        self.assertEqual(config.config['animal'], 'cat')
        self.assertEqual(config.animal, 'cat')
        self.assertListEqual(config.values, ['a', 'b', 'c', 23])
        # if no value is provided, the default kicks in
        self.assertEqual(config.foobar, 'barfoo')

    def test_configParser_allowed_values(self):
        """Allowed values"""
        config = config_parser.configParser(
            self.config_file,
            allowed_values = {'animal': ['cat', 'dog', 'snake']}
        )
        with self.assertRaises(config_parser.IllegalConfigValue):
            config_parser.configParser(
                self.config_file,
                allowed_values = {'animal': ['dog', 'snake']})

    def test_configParser_required_keys(self):
        """Required keys"""
        config = config_parser.configParser(
            self.config_file,
            required_keys = ['animal', 'location']
        )
        with self.assertRaises(config_parser.MissingConfigValue):
            config_parser.configParser(
                self.config_file,
                required_keys = ['animal', 'location', 'foobar'])

