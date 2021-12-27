import hashlib
import os.path
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
