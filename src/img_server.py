import threading
import time
from queue import Queue

from PySide6.QtCore import Signal, QObject
from loguru import logger as log

from pkg.tencent_cos.cos import TencentCos
from pkg.tencent_cos.cos_bucket import TencentCosBucket
from pkg.tencent_cos.exceptions import CosBucketNotFoundError
from src.config_loader import ConfigLoader


class ImageServer(QObject):
    """图片服务器相关"""
    # Signal and Slots
    bucket_list = Signal(list)
    dir_list = Signal(list)
    check_result = Signal(bool, str)
    check_buckets_finished = Signal()
    check_dirs_finished = Signal()

    def __init__(self):
        super().__init__()
        self.event_queue = Queue()
        self.config = ConfigLoader().read_config()
        self.cos_client = None
        self.cos_bucket = None
        self._t = None

    def _reload_config(self):
        self.config = ConfigLoader().read_config()

    def _is_server_config_changed(self):
        latest_config = ConfigLoader().read_config()
        if latest_config.cos.tencent.secret_id != self.config.cos.tencent.secret_id:
            log.warning('User config cos.tencent.secret_id changed')
            return True
        elif latest_config.cos.tencent.secret_key != self.config.cos.tencent.secret_key:
            log.warning('User config cos.tencent.secret_key changed')
            return True
        else:
            return False

    def reconnect_server(self):
        """连接到腾讯COS，获取存储桶信息"""
        if self._is_server_config_changed() or \
                (not isinstance(self.cos_client, TencentCos)):
            self._reload_config()
            self.cos_client = None
            self.cos_bucket = None
            try:
                self.cos_client = TencentCos(
                    self.config.cos.tencent.secret_id, self.config.cos.tencent.secret_key)
                log.info('reconnect server success')
                return True
            except Exception as e:
                log.error(f'reconnect server error, detail: {str(e)}')
                return False
        else:
            log.warning(self._is_server_config_changed())
            log.warning(isinstance(self.cos_client, TencentCos))
            log.info('reconnect server skipped')
            return True

    def connect_bucket(self, bucket_name: str):
        """连接到COS存储桶"""
        if not self.reconnect_server():
            return False
        elif isinstance(self.cos_bucket, TencentCosBucket):
            return self._validate_bucket(bucket_name)
        else:
            return self._reconnect_bucket(bucket_name)

    def _validate_bucket(self, bucket_name: str):
        if bucket_name == self.cos_bucket.name:
            log.info(f'Already connected to {bucket_name}.')
            return True
        elif bucket_name not in self.cos_client.list_buckets():
            log.error(f'Cannot find bucket: {bucket_name}')
            return False
        else:
            return self._reconnect_bucket(bucket_name)

    def _reconnect_bucket(self, bucket_name: str):
        try:
            self.cos_bucket = TencentCosBucket(self.cos_client, bucket_name)
            log.info(f'Connect to cos bucket {bucket_name} success!')
            return True
        except Exception as e:
            log.error(str(e))
            return False

    def list_bucket(self):
        """连接到腾讯COS，获取存储桶列表"""
        try:
            self.reconnect_server()
            self.check_result.emit(True, '')
            self.bucket_list.emit(self.cos_client.list_buckets())
        except Exception as e:
            self.check_result.emit(False, str(e))
        finally:
            self.check_buckets_finished.emit()

    def list_dirs(self, bucket_name: str):
        """连接到腾讯COS，获取存储桶文件夹列表"""
        if not bucket_name:
            log.warning(f'invalid bucket name: {str(bucket_name)}')
            self.dir_list.emit([])
            self.check_dirs_finished.emit()
        else:
            # 避免因直接运行函数导致的UI卡顿，另起一个线程
            self._t = threading.Thread(target=self._list_dirs, args=(bucket_name, ))
            self._t.start()

    def _list_dirs(self, bucket_name: str):
        if self.connect_bucket(bucket_name):
            self.dir_list.emit(self.cos_bucket.list_dirs())
            self.check_dirs_finished.emit()
        else:
            self.dir_list.emit([])
            self.check_dirs_finished.emit()
