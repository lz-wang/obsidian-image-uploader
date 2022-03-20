import os
import platform
from pathlib import Path
from loguru import logger as log

APP_NAME = 'ObsidianImageUploader'
USER_HOME = Path.home()
DEFAULT_CONFIG_PATH = os.path.join(USER_HOME, '.config', 'obsidian-img-uploader')
OS = platform.system()


def show_env():
    log.info(f'OS: {OS}')
    log.info(f'APP_NAME: {APP_NAME}')
    log.info(f'USER_HOME: {USER_HOME}')
    log.info(f'DEFAULT_CONFIG_PATH: {DEFAULT_CONFIG_PATH}')
