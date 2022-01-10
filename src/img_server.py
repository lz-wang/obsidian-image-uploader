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
            self.cos_client = TencentCos(self.config.cos.tencent.secret_id,
                                         self.config.cos.tencent.secret_key)
            return True
        else:
            return False

    def connect_bucket(self, bucket_name: str):
        """连接到COS存储桶"""
        if not self.reconnect_server() and isinstance(self.cos_bucket, TencentCosBucket):
            # 如果已经连上此存储桶，无需重复连接bucket
            if bucket_name == self.cos_bucket.name:
                log.info(f'Already connected to {bucket_name}.')
            elif bucket_name not in self.cos_client.list_buckets():
                raise CosBucketNotFoundError(f'找不到存储桶: {bucket_name}')
            else:
                self.cos_bucket = TencentCosBucket(self.cos_client, bucket_name)
                log.info(f'Connect to {bucket_name} success!')
        else:
            self.cos_bucket = TencentCosBucket(self.cos_client, bucket_name)
            log.info(f'Connect to cos bucket {bucket_name} success!')

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
            self.dir_list.emit([])
            self.check_dirs_finished.emit()
        else:
            # 避免因直接运行函数导致的UI卡顿，另起一个线程
            t = threading.Thread(target=self._list_dirs, args=(bucket_name, ))
            t.start()

    def _list_dirs(self, bucket_name: str):
        self.connect_bucket(bucket_name)
        self.dir_list.emit(self.cos_bucket.list_dirs())
        self.check_dirs_finished.emit()

    def run(self):
        while True:
            time.sleep(0.1)
            if self.event_queue.qsize() > 0:
                event = self.event_queue.get()
                log.info(f'receive event: {event}')
                if event['type'] == 'LIST_BUCKET':
                    self.list_bucket(event['cos'])
                elif event['type'] == 'LIST_FILES':
                    self.list_dirs(event['bucket'])
                else:
                    raise TypeError(f'Unknown event: {event}')
