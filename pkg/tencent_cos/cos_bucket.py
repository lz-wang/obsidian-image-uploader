import os
from urllib.parse import quote

from qcloud_cos import CosServiceError

from pkg.tencent_cos.cos import TencentCos
from pkg.tencent_cos.exceptions import CosBucketDirNotFoundError
from pkg.utils.file_tools import get_file_md5sum
from pkg.utils.logger import get_logger

REGIONS = ['nanjing', 'chengdu', 'beijing', 'guangzhou', 'shanghai', 'chongqing', 'hongkong']


class TencentCosBucket(object):
    """腾讯云COS桶文件操作"""
    def __init__(self, cos: TencentCos, bucket_name):
        self.cos = cos
        self.log = get_logger(f'{self.__class__.__name__}')
        self.name = bucket_name
        self.full_name = bucket_name + '-' + self.cos.get_appid()
        self.base_url = self.get_bucket_url()
        self.get_correct_cos_region()

    def get_bucket_url(self):
        """获取存储桶URL"""
        return 'https://' + self.full_name + '.cos.' + self.cos.region + '.myqcloud.com/'

    def get_correct_cos_region(self):
        """获取存储桶的正确地区配置"""
        for region in REGIONS:
            try:
                self.cos.client.list_objects(Bucket=self.full_name)
                break
            except CosServiceError as e:
                if e.get_error_code() == 'NoSuchBucket':
                    self.log.warning(f'bucket {self.name} not in region '
                                     f'{self.cos.region}, try another region')
                    region = f'ap-{region}'
                    self.cos = TencentCos(self.cos.secret_id, self.cos.secret_key, region)
                    self.full_name = self.name + '-' + self.cos.get_appid()
                    continue
            except Exception as e:
                self.log.error(f'Fatal: {str(e)}')

    def list_objects(self, prefix: str = ''):
        """列出远程对象/文件"""
        response = self.cos.client.list_objects(Bucket=self.full_name, Prefix=prefix)
        if 'Contents' in response:
            return [c['Key'].replace(prefix, '') for c in response['Contents']]
        else:
            self.log.warning(f'Cannot find any objects in bucket {self.name}')
            return []

    def list_dirs(self):
        """列出所有远程文件夹"""
        return [ob[:-1] for ob in self.list_objects() if ob.endswith('/')]

    def list_files(self):
        """列出所有远程文件"""
        return [ob for ob in self.list_objects() if not ob.endswith('/')]

    def list_dir_files(self, remote_dir: str):
        """列出特定文件夹下远程文件"""
        if remote_dir not in ['', '/']:
            if not remote_dir.endswith('/'):
                remote_dir += '/'
            if remote_dir[:-1] not in self.list_dirs():
                raise CosBucketDirNotFoundError(f'Bucket dir {remote_dir} not found.')
        return self.list_objects(prefix=remote_dir)

    def upload_object(self, local_path, remote_path: str = '', overwrite=True):
        """上传单个对象"""
        object_key = local_path.split('/')[-1]
        if not os.path.exists(local_path):
            return False, f'local path: {local_path} doesnt exists'
        if object_key in self.list_objects():
            if not overwrite:
                warning_msg = f'{object_key} already in {self.name}, skipped!'
                self.log.warning(warning_msg)
                return True, warning_msg
            else:
                self.log.warning(f'{object_key} already in {self.name}, overwrite!')
        try:
            with open(local_path, 'rb') as f:
                self.cos.client.put_object(
                    Bucket=self.full_name,
                    Body=f,
                    Key=remote_path + object_key,
                    StorageClass='STANDARD',
                    EnableMD5=True,
                    Metadata={'x-cos-meta-md5': get_file_md5sum(local_path)}
                )
            self.log.info(f'Upload {local_path} to {remote_path} Success!')
        except CosServiceError as e:
            return False, e.get_error_code()
        except Exception as e:
            return False, str(e)

        return True, 'SUCCESS'

    def download_object(self, remote_file_path, local_folder):
        """下载单个对象"""
        file_path, file_name = self.get_object_path_name(remote_file_path)
        local_file_path = os.path.join(local_folder, file_name)
        try:
            self.cos.client.download_file(
                Bucket=self.full_name,
                Key=remote_file_path,
                DestFilePath=local_file_path
            )
            self.log.info(f'Download {file_name} to {local_file_path} success!')
        except Exception as e:
            self.log.error(f'Download {file_name} to {local_file_path} failed! (detail: {str(e)})')

    def _delete_object(self, object_full_path: str):
        """删除指定路径对象"""
        self.log.warning(f'Bucket {self.name}, delete object: {object_full_path}')
        self.cos.client.delete_object(
            Bucket=self.full_name,
            Key=object_full_path
        )

    def delete_object(self, remote_dir, object_key):
        """删除文件夹内的单个对象"""
        if not remote_dir.endswith('/') and remote_dir != '':
            remote_dir += '/'
        if object_key not in self.list_dir_files(remote_dir):
            err_msg = f'{object_key} not found in {remote_dir}'
            self.log.error(err_msg)
            return False, err_msg
        else:
            self._delete_object(remote_dir+object_key)
            return True, ''

    def delete_dir_objects(self, remote_dir: str):
        """删除文件夹内所有对象"""
        for file in self.list_dir_files(remote_dir):
            self._delete_object(file)

    def delete_all_objects(self):
        """删除所有文件，清空存储桶"""
        for file in self.list_files():
            paths = file.split('/')
            file_name = paths[-1]
            if len(paths) == 1:
                file_path = ''
            else:
                file_path = '/'.join(paths[:-1])
            self.delete_object(file_path, file_name)
        self.log.warning(f'Bucket {self.name} all files has been deleted')

    def get_object_md5hash(self, object_full_path: str):
        """获取文件md5哈希值 https://cloud.tencent.com/document/product/436/36427"""
        response = self._get_object_info(object_full_path)
        md5hash = response['x-cos-meta-md5']
        self.log.info(f'Bucket file: {object_full_path}, md5: {md5hash}')
        return md5hash

    def _get_object_info(self, object_full_path: str):
        """获取对象元数据信息"""
        return self.cos.client.get_object(
            Bucket=self.full_name,
            Key=object_full_path
        )

    def get_object_url(self, remote_path: str, object_key: str):
        """获取指定对象的URL"""
        object_url = self.base_url + quote(remote_path+object_key)
        self.log.info(f'get {remote_path+object_key} url: {object_url}')

        return object_url

    @staticmethod
    def get_object_path_name(object_full_path: str):
        """根据对象的全路径获取所在文件夹和文件名"""
        if '/' not in object_full_path:
            return '', object_full_path
        else:
            paths = object_full_path.split('/')
            return '/'.join(paths[:-1]), paths[-1]
