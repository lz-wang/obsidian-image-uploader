import copy
import os
import yaml
import shutil

from pkg.utils.logger import get_logger

DEFAULT_CONFIG_PATH = os.path.join(
    os.environ['HOME'], '.config/obsidian-img-uploader')
DEFAULT_CONFIG = {
    'cos': {
        'tencent': {
            'bucket': 'obsidian',
            'dir': 'obsidian',
            'secret_id': 'xxx',
            'secret_key': 'xxx'
        }
    },
    'obsidian': {
        'attachment_path': '/',
        'note_default_path': '/',
        'overwrite_suffix': '_new',
        'recent_not_path': '/',
        'vault_path': '/'
    }
}


class ConfigLoader(object):
    def __init__(self, config_file=None):
        self.log = get_logger(self.__class__.__name__)
        self.config_file = self._get_config_file(config_file)
        self.config = {}

    def _get_config_file(self, config_file):
        if config_file is not None:
            return config_file
        return self.init_config()

    def read_config(self):
        with open(self.config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        return self.config

    def update_config(self, new_config=None):
        new_config = self.config if new_config is None else new_config
        with open(self.config_file, 'w') as f:
            yaml.safe_dump(new_config, f)

    def init_config(self):
        user_config = os.path.join(DEFAULT_CONFIG_PATH, 'app_config.yaml')
        if os.path.exists(user_config) and self.check_user_config(user_config):
            self.log.info(f'check user config in {user_config} format success')
        else:
            self.log.warning(f'check user config in {user_config} format failed')
            shutil.rmtree(DEFAULT_CONFIG_PATH, ignore_errors=True)
            os.makedirs(DEFAULT_CONFIG_PATH, exist_ok=True)
            with open(user_config, 'w') as f:
                yaml.safe_dump(DEFAULT_CONFIG, f)
            self.log.info(f'init user config in {user_config} format success')

        return user_config

    def check_user_config(self, user_config_path):
        try:
            with open(user_config_path, 'r') as f:
                uc = yaml.safe_load(f)
                dc = copy.deepcopy(DEFAULT_CONFIG)
                self.compare_dict_keys(dc, uc)
        except Exception as e:
            self.log.warning(f'check user config in {user_config_path} '
                             f'format error, detail: {str(e)}')
            return False

    def compare_dict_keys(self, d1: dict, d2: dict):
        k1 = sorted(d1.keys())
        k2 = sorted(d2.keys())
        assert k2 == k1, f'{k2} != {k1}'

        for k in k1:
            type1 = type(d1[k])
            assert isinstance(d2[k], type1), f'{d2[k]} != {d1[k]}'

            if isinstance(type1, dict):
                self.compare_dict_keys(d1[k], d2[k])
