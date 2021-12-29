import os
import time
from datetime import datetime
from queue import Queue

from PySide6.QtCore import QThread, Signal

from pkg.tencent_cos.cos import TencentCos
from pkg.tencent_cos.cos_bucket import TencentCosBucket
from pkg.utils.logger import get_logger
from pkg.utils.file_tools import get_file_md5sum
from src.config_loader import ConfigLoader
from pkg.tencent_cos.exceptions import CosBucketNotFoundError, CosBucketDirNotFoundError


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
        self.log = get_logger()
        self.cos = None
        self.bucket = None
        self.bucket_name = bucket_name
        self.local_files = local_files
        self.remote_dir = remote_dir
        self.check_md5 = False
        self.last_checked_synced_files = []
        self.file_url_dict = {file: None for file in self.local_files}
        self.event_queue = Queue()

    def connect_server(self):
        """连接到腾讯COS，获取存储桶信息"""
        if not isinstance(self.cos, TencentCos):
            config = ConfigLoader().read_config()
            secret_id = config.cos.tencent.secret_id
            secret_key = config.cos.tencent.secret_key
            self.cos = TencentCos(secret_id, secret_key)

    def connect_bucket(self):
        """连接到COS存储桶"""
        self.connect_server()
        if self.bucket_name not in self.cos.list_buckets():
            raise CosBucketNotFoundError(f'找不到存储桶: {self.bucket_name}')
        self.bucket = TencentCosBucket(self.cos, self.bucket_name)

    def connect_bucket_dir(self):
        """连接到腾讯COS，获取存储桶信息"""
        self.connect_bucket()
        bucket_dirs = self.bucket.list_dirs()
        bucket_dirs = [''] if not bucket_dirs else bucket_dirs
        self.log.info(f'config remote_dir -> {self.remote_dir}, cos dirs -> {bucket_dirs}')
        if self.remote_dir not in bucket_dirs:
            raise CosBucketDirNotFoundError(f'在存储桶{self.bucket_name}中找不到{self.remote_dir}目录')

    def _get_remote_files(self):
        self.connect_bucket()
        return self.bucket.list_dir_files(self.remote_dir)

    def run(self):
        """启动子线程，将文件上传到COS，同时发送信号到GUI"""
        self.connect_bucket_dir()
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

    def check_file(self, local_file: str):
        """校验是否有相同文件已存在于cos指定文件夹上"""
        self.connect_bucket()
        assert isinstance(self.bucket, TencentCosBucket)
        remote_file_path = self.remote_dir+'/'+local_file.split('/')[-1]
        if not self.bucket.is_object_exists(remote_file_path):
            return False, f'在存储桶{self.bucket_name}的{self.remote_dir}目录中找不到{local_file}文件'
        local_file_md5 = get_file_md5sum(local_file)
        remote_file_md5 = self.bucket.get_object_md5hash(remote_file_path)
        if local_file_md5 != remote_file_md5:
            return False, f'文件{local_file}的MD5哈希校验不通过，远程存在同名文件'
        return True, ''

    def check_files(self, remote_files):
        """检查文件同步状态"""
        self.console_log_text.emit('正在检查文件同步状态：')
        has_not_synced = False
        if self.check_md5 is True:
            self.last_checked_synced_files.clear()
        for i in range(len(self.local_files)):
            local_file = self.local_files[i]
            local_file_name = local_file.split("/")[-1]
            check_msg = f'[{i+1}/{len(self.local_files)}] '
            # 检查文件是否存在于远端
            if local_file_name not in remote_files:
                sync_status = False
                err_msg = '' if sync_status else \
                    f'警告: 在存储桶{self.bucket_name}的{self.remote_dir}' \
                    f'目录中找不到{local_file_name}文件'
            else:  # 如果开启MD5校验则检查MD5
                if self.check_md5 is True:
                    sync_status, err_msg = self.check_file(local_file)
                else:
                    sync_status, err_msg = True, ''

            if sync_status is False:
                check_msg += err_msg
                has_not_synced = True
            else:
                check_msg += f'文件已同步: {local_file_name}'
                if local_file not in self.last_checked_synced_files:
                    self.last_checked_synced_files.append(local_file)

            self.check_result.emit(check_msg)
            self.console_log_text.emit(check_msg)

        if not has_not_synced:
            self.console_log_text.emit('全部文件已同步!')
        else:
            self.console_log_text.emit(
                f'已同步文件数目: {len(self.last_checked_synced_files)}/{len(self.local_files)}')

        current_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.check_result.emit(f'已同步{len(self.last_checked_synced_files)}/{len(self.local_files)}, '
                               f'检查时间{current_time}')

    def upload_files(self, remote_files):
        """将本地文件上传到服务器"""
        file_num = len(self.local_files)
        self.upload_progress_max_value.emit(file_num)
        for i in range(file_num):
            msg = ''
            local_file = self.local_files[i]
            file_name = local_file.split('/')[-1]
            msg += f'正在上传文件({i+1}/{file_num})\n    '
            assert os.path.isfile(local_file), f'can not find file {local_file}!'

            # 如果远端没有此文件，直接上传
            if file_name not in remote_files:
                self.bucket.upload_object(local_path=local_file, remote_path=self.remote_dir + '/')
                msg += f'(上传成功)本地文件: {local_file} \n    '
            else:
                # 如果没有开启MD5校验，跳过上传
                if self.check_md5 is False:
                    msg += f'(远程已存在)本地文件: {local_file} \n    '
                else:
                    # 如果开启MD5校验，且上次检查同步的结果还在，直接从缓存读取
                    if local_file in self.last_checked_synced_files:
                        msg += f'(远程已存在)本地文件: {local_file} \n    '
                    # 否则重新校验文件，耗时较长
                    else:
                        sync_status, err_msg = self.check_file(local_file)
                        if sync_status:  # 校验成功，跳过上传
                            msg += f'(远程已存在)本地文件: {local_file} \n    '
                        else:  # 校验失败，覆盖式上传
                            self.log.warning(err_msg)
                            self.bucket.upload_object(local_path=local_file, remote_path=self.remote_dir + '/')
                            msg += f'(上传覆盖成功)本地文件: {local_file} \n    '
            file_url = self.bucket.get_object_url(remote_path=self.remote_dir+'/', object_key=file_name)
            msg += f'远程URL: {file_url}'
            self.file_url_dict[local_file] = file_url
            self.console_log_text.emit(msg)
            self.upload_progress_value.emit(i+1)
        self.files_url.emit(self.file_url_dict)

