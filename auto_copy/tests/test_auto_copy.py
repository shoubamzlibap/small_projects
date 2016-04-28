# test_auto_copy.py
# tests for auto_copy.py

import unittest
from .. import auto_copy

class testAutocopy(unittest.TestCase):

    def test_config_reader(self):
        """Config is read"""
        config = auto_copy.read_config('auto_copy.yml.example')
        self.assertEqual(config.rip_speed, 'veryslow')
        self.assertEqual(config.max_tracks, 10)
        self.assertTrue(isinstance(config.max_tracks, int))


