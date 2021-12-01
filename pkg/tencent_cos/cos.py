from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos import CosServiceError
from pkg.utils.logger import get_logger


class TencentCos(object):
    """腾讯云COS接口类封装。
    参考：https://cloud.tencent.com/document/product/436/12269
    """

    def __init__(self, secret_id: str, secret_key: str,
                 region: str = 'ap-chengdu'):
        """secret_id和secret_key获取参考：
        https://console.cloud.tencent.com/cam/capi"""
        self.log = get_logger(f'{self.__class__.__name__}')
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.client = self.connect_client()
        self._bucket_suffix = self.get_suffix_id()

    def connect_client(self, region=None):
        cos_region = self.region if region is None else region
        cos_config = CosConfig(SecretId=self.secret_id, SecretKey=self.secret_key,
                               Region=cos_region, Token=None, Scheme='https')
        return CosS3Client(cos_config)

    def get_suffix_id(self):
        """获取cos桶的默认后缀名"""
        demo_bucket = self.client.list_buckets()['Buckets']['Bucket'][0]
        return demo_bucket['Name'].split('-')[-1]

    def list_buckets(self):
        """获取无默认桶后缀名的cos桶列表"""
        raw_buckets = self.client.list_buckets()
        buckets = [bucket['Name'] for bucket in raw_buckets['Buckets']['Bucket']]
        return [b.replace(f'-{self._bucket_suffix}', '') for b in buckets]

    def create_bucket(self, bucket_name):
        """创建新的cos桶"""
        # 检查是否已存在此cos桶
        before_created = self.list_buckets()
        if bucket_name in before_created:
            return False, f'{bucket_name} 已存在于现有存储桶列表({", ".join(before_created)})'

        try:
            self.client.create_bucket(self._fmt_b_name(bucket_name))
        except CosServiceError as e:
            return False, e.get_error_code()

        # 检测是否新建桶成功
        after_created = self.list_buckets()
        if bucket_name in after_created:
            return True, f'创建桶{bucket_name}成功，现有存储桶列表({", ".join(after_created)})'

    def delete_bucket(self, bucket_name):
        """删除空的cos桶"""
        try:
            self.client.delete_bucket(Bucket=self._fmt_b_name(bucket_name))
        except CosServiceError as e:
            return False, e.get_error_code()
        except Exception as e:
            return False, str(e)
        return True, f'删除桶{bucket_name}成功，现有存储桶列表({", ".join(self.list_buckets())})'

    def _fmt_b_name(self, bucket_name):
        return bucket_name + '-' + self._bucket_suffix

    def rebuild_bucket(self, bucket_name):
        """TODO: 清空、删除并新建cos桶"""
        pass
