import os
from urllib.parse import quote

from pkg.tencent_cos.cos import TencentCos
from qcloud_cos import CosServiceError
from pkg.utils.logger import get_logger

REGIONS = ['nanjing', 'chengdu', 'beijing', 'guangzhou', 'shanghai', 'chongqing', 'hongkong']


class TencentCosBucket(object):
    """腾讯云COS桶文件操作"""
    def __init__(self, cos: TencentCos, bucket_name):
        self.cos = cos
        self.log = get_logger(f'{self.__class__.__name__}')
        self.name = bucket_name
        self.full_name = bucket_name + '-' + self.cos.get_suffix_id()
        self.base_url = self.get_bucket_url()
        self.get_correct_cos_region()

    def get_bucket_url(self):
        return 'https://' + self.full_name + '.cos.' + self.cos.region + '.myqcloud.com/'

    def get_correct_cos_region(self):
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
                    self.full_name = self.name + '-' + self.cos.get_suffix_id()
                    continue
            except Exception as e:
                self.log.error(f'Fatal: {str(e)}')

    def list_objects(self, prefix: str = ''):
        """列出对象"""
        response = self.cos.client.list_objects(Bucket=self.full_name, Prefix=prefix)
        if 'Contents' in response:
            return [c['Key'].replace(prefix, '') for c in response['Contents']]
        else:
            self.log.warning(f'在cos桶{self.name}上找不到任何对象')
            return []

    def list_dirs(self):
        """列出远程目录"""
        contents = self.list_objects()
        dirs = []
        for c in contents:
            if '/' not in c:
                continue
            else:
                dirs.append('/'.join(c.split('/')[:-1]))
        return list(set(dirs))

    def upload_object(self, local_path, remote_path: str = '', overwrite=True):
        """上传单个对象"""
        object_key = local_path.split('/')[-1]
        if not os.path.exists(local_path):
            return False, f'{local_path}不存在'
        if object_key in self.list_objects():
            if not overwrite:
                self.log.warning(f'{object_key} already in {self.name}, skipped!')
                return True
            else:
                self.log.warning(f'{object_key} already in {self.name}, overwrite!')
        try:
            with open(local_path, 'rb') as f:
                self.cos.client.put_object(
                    Bucket=self.full_name,
                    Body=f,
                    Key=remote_path + object_key,
                    StorageClass='STANDARD',
                    EnableMD5=False
                )
            self.log.info(f'Upload {local_path} to {remote_path} Success!')
        except CosServiceError as e:
            return False, e.get_error_code()
        except Exception as e:
            return False, str(e)

        return True, 'SUCCESS'

    def download_object(self, remote_path, local_path):
        """TODO: 下载单个对象"""
        pass

    def delete_object(self, remote_path, object_key):
        """删除单个对象"""
        if object_key not in self.list_objects(prefix=remote_path):
            err_msg = f'{object_key} not found in {remote_path}'
            self.log.error(err_msg)
            return False, err_msg
        else:
            self.log.info(f'{object_key} found in {remote_path}')
        self.cos.client.delete_object(
            Bucket=self.full_name,
            Key=remote_path+object_key
        )

    def get_object_url(self, remote_path: str, object_key: str):
        object_url = self.base_url + quote(remote_path+object_key)
        self.log.info(f'get {remote_path+object_key} url: {object_url}')

        return object_url
