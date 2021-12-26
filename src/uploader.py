import os
import time
from datetime import datetime
from queue import Queue

from PySide6.QtCore import QThread, Signal

from pkg.tencent_cos.cos import TencentCos
from pkg.tencent_cos.cos_bucket import TencentCosBucket
from src.config_loader import ConfigLoader


class Uploader(QThread):
    """上传一组文件到腾讯COS，与GUI联动的QT子线程类"""
    upload_progress_max_value = Signal(int)
    upload_progress_value = Signal(int)
    console_log_text = Signal(str)
    files_url = Signal(dict)
    check_result = Signal(str)

    def __init__(self, bucket_name: str, local_files: list, remote_dir: str):
        """init"""
        super(Uploader, self).__init__()
        self.cos = None
        self.bucket = None
        self.bucket_name = bucket_name
        self.local_files = local_files
        self.remote_dir = remote_dir
        self.file_url_dict = {file: None for file in self.local_files}
        self.event_queue = Queue()

    def connect_bucket(self):
        """连接到腾讯COS，获取存储桶信息，如果桶不存在则创建"""
        self.connect_server()
        if self.bucket_name not in self.cos.list_buckets():
            self.cos.create_bucket(self.bucket_name)
        self.bucket = TencentCosBucket(self.cos, self.bucket_name)

    def connect_server(self):
        """连接到腾讯COS，获取存储桶信息"""
        config = ConfigLoader().read_config()
        secret_id = config['cos']['tencent']['secret_id']
        secret_key = config['cos']['tencent']['secret_key']
        self.cos = TencentCos(secret_id, secret_key)

    def _get_remote_files(self):
        if self.bucket is None:
            self.connect_bucket()
        return self.bucket.list_objects(prefix=self.remote_dir)

    def run(self):
        """启动子线程，将文件上传到COS，同时发送信号到GUI"""
        self.connect_bucket()
        while True:
            time.sleep(0.1)
            if self.event_queue.qsize() > 0:
                event = self.event_queue.get()
                remote_files = self._get_remote_files()
                if event == 'UPLOAD':
                    self.upload_files(remote_files)
                elif event == 'CHECK':
                    self.check_files(remote_files)
                else:  # ignore
                    pass

    def check_files(self, remote_files):
        synced_files = [f for f in self.local_files if f.split('/')[-1] in remote_files]
        msg = '正在检查文件同步状态：'
        has_not_synced = False
        for f in self.local_files:
            if f not in synced_files:
                msg += f'\n发现未同步文件: {f}'
                has_not_synced = True
        if not has_not_synced:
            msg += f'全部文件已同步！'
        self.console_log_text.emit(msg)
        current_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.check_result.emit(f'已同步{len(synced_files)}/{len(self.local_files)}, '
                               f'检查时间{current_time}')
        return

    def upload_files(self, remote_files):
        file_num = len(self.local_files)
        self.upload_progress_max_value.emit(file_num)
        for i in range(file_num):
            msg = ''
            file_path = self.local_files[i]
            file_name = file_path.split('/')[-1]
            msg += f'正在上传文件({i+1}/{file_num})\n    '
            assert os.path.isfile(file_path), f'can not find file {file_path}!'
            if file_name in remote_files:
                msg += f'(远程已存在)本地文件: {file_path} \n    '
            else:
                msg += f'(上传成功)本地文件: {file_path} \n    '
                self.bucket.upload_object(local_path=file_path, remote_path=self.remote_dir)
            file_url = self.bucket.get_object_url(remote_path=self.remote_dir, object_key=file_name)
            msg += f'远程URL: {file_url}'
            self.file_url_dict[file_path] = file_url
            self.console_log_text.emit(msg)
            self.upload_progress_value.emit(i+1)
        self.files_url.emit(self.file_url_dict)

