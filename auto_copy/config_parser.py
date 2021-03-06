"""
config_parser.py
An attempt at a simple yaml based config parser class
"""

import yaml

class IllegalConfigValue(Exception): pass


class MissingConfigValue(Exception): pass


class configParser(object):
    """
    Read a yaml file and provide the options defined therein as attributes.
    Allow setting of defaults, allowed values and required keys.
    """

    def __init__(self, config_file, defaults=None, allowed_values=None, required_keys=None):
        """
        Create the configParser object, set defaults and check if the config matches the
        specified conditions.

        config_file: path to a yaml file
        defaults: a dict containing default values. optional
        allowed_values: a dict containing lists of allowed values. optional
        required_keys: a list of keys that must be contained in the yaml file.

        """
        if defaults is None: defaults = {}
        if allowed_values is None: allowed_values = {}
        if required_keys is None: required_keys = []
        # defaults
        for key, value in defaults.items():
            setattr(self, key, value)
        self.config_file = config_file
        # parsing config file
        with open(self.config_file, 'r') as cfile:
            self.config = yaml.safe_load(cfile)
        for key, value in self.config.items():
            setattr(self, key, value)
        # allowed values
        for key, value in allowed_values.items():
            if self.config[key] not in value:
                raise IllegalConfigValue('Illegal configuration value for "' +
                                         str(key) + '": ' + str(self.config[key]))
        # required keys
        for key in required_keys:
            if not self.__dict__.get(key):
                raise MissingConfigValue('The following key is missing in ' +
                                         self.config_file + ': ' + str(key))

