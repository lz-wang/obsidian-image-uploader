import hashlib
import os.path
import pathlib
from functools import partial


def get_file_md5sum(file_path: str):
    """获取文件的md5哈希值"""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f'cannot found file: {file_path}')
    with open(file_path, 'rb') as f:
        md5hash = hashlib.md5()
        for buffer in iter(partial(f.read, 128), b''):
            md5hash.update(buffer)
        return md5hash.hexdigest()


def touch_empty_file(file_name: str = '.tmp', file_dir: str = ''):
    """在指定目录创建空文件"""
    if not os.path.exists(file_dir):
        file_dir = os.environ['HOME']
    file_path = os.path.join(file_dir, file_name)
    pathlib.Path(file_path).touch(exist_ok=True)
    return file_path
