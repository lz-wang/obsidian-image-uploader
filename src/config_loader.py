import os
import yaml

from pkg.utils.logger import get_logger


class ConfigLoader(object):
    def __init__(self, config_file=None):
        self.log = get_logger(self.__class__.__name__)
        self.config_file = self._get_config_file(config_file)
        self.config = {}

    @staticmethod
    def _get_config_file(config_file):
        if config_file is not None:
            return config_file
        return os.path.join(os.getcwd(), 'config.yaml')

    def read_config(self):
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        return self.config

    def update_config(self, new_config=None):
        new_config = self.config if new_config is None else new_config
        with open(self.config_file, 'w') as f:
            yaml.safe_dump(new_config, f)

