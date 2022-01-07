import time
from queue import Queue

from PySide6.QtCore import QThread, Signal

from pkg.tencent_cos.cos import TencentCos
from pkg.tencent_cos.cos_bucket import TencentCosBucket
from loguru import logger

from src.config_loader import ConfigLoader


class ImageServer(QThread):
    """上传一组文件到腾讯COS，与GUI联动的QT子线程类"""
    tip_text = Signal(str)
    bucket_list = Signal(list)
    dir_list = Signal(list)
    check_result = Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.log = logger
        self.event_queue = Queue()
        self.cos = None

    def list_bucket(self, cos_type):
        """连接到腾讯COS，获取存储桶列表"""
        if cos_type == 'tencent':
            config = ConfigLoader().read_config()
            secret_id = config.cos.tencent.secret_id
            secret_key = config.cos.tencent.secret_key
            try:
                self.cos = TencentCos(secret_id, secret_key)
                self.check_result.emit(True, '')
                self.bucket_list.emit(self.cos.list_buckets())
            except Exception as e:
                self.check_result.emit(False, str(e))
        else:
            raise TypeError(f'Unknown cos type: {cos_type}')

    def list_dirs(self, bucket_name):
        """连接到腾讯COS，获取存储桶文件夹列表"""
        if not bucket_name:
            self.dir_list.emit([])
        if not self.cos:
            self.dir_list.emit([])

        cos_bucket = TencentCosBucket(self.cos, bucket_name)
        self.dir_list.emit(cos_bucket.list_dirs())

    def run(self):
        while True:
            time.sleep(0.1)
            if self.event_queue.qsize() > 0:
                event = self.event_queue.get()
                self.log.info(f'receive event: {event}')
                if event['type'] == 'LIST_BUCKET':
                    self.list_bucket(event['cos'])
                elif event['type'] == 'LIST_FILES':
                    self.list_dirs(event['bucket'])
                else:
                    raise TypeError(f'Unknown event: {event}')
