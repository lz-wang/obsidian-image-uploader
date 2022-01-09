from qcloud_cos import CosConfig, CosS3Client, CosServiceError

from loguru import logger as log


class TencentCos(object):
    """腾讯云COS接口类封装
    参考：https://cloud.tencent.com/document/product/436/12269
    """

    def __init__(self, secret_id: str, secret_key: str, region: str = 'ap-chengdu'):
        """secret_id和secret_key获取参考：
        https://console.cloud.tencent.com/cam/capi"""
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region
        self.client = self.connect_client()
        self._bucket_suffix = self.get_appid()

    def connect_client(self, region=None):
        """连接到COS服务"""
        cos_region = self.region if region is None else region
        cos_config = CosConfig(SecretId=self.secret_id, SecretKey=self.secret_key,
                               Region=cos_region, Token=None, Scheme='https')
        return CosS3Client(cos_config)

    def get_appid(self):
        """获取cos的APPID"""
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
        if self.check_bucket_exists(bucket_name):
            return False, f'Bucket {bucket_name} already exists，' \
                          f'current bucket list -> ({", ".join(self.list_buckets())})'

        try:
            self.client.create_bucket(self._fmt_b_name(bucket_name))
        except CosServiceError as e:
            return False, e.get_error_code()

        # 检测是否新建桶成功
        after_created = self.list_buckets()
        if bucket_name in after_created:
            return True, f'Create bucket {bucket_name} success，' \
                         f'current bucket list -> ({", ".join(after_created)})'

    def delete_bucket(self, bucket_name):
        """删除空的cos桶"""
        try:
            self.client.delete_bucket(Bucket=self._fmt_b_name(bucket_name))
            success_msg = f'Delete bucket {bucket_name} success, ' \
                          f'current bucket list -> ({", ".join(self.list_buckets())})'
            log.info(success_msg)
            return True, success_msg
        except CosServiceError as e:
            err_msg = f'Delete bucket {bucket_name} failed，detail: {e.get_error_code()}'
            log.error(err_msg)
            return False, err_msg
        except Exception as e:
            err_msg = f'Delete bucket {bucket_name} failed，detail: {str(e)}'
            log.error(err_msg)
            return False, err_msg

    def check_bucket_exists(self, bucket_name: str):
        """检查cos桶是否存在"""
        return self.client.bucket_exists(self._fmt_b_name(bucket_name))

    def _fmt_b_name(self, bucket_name):
        """归一化cos桶名称为带后缀形式"""
        return bucket_name + '-' + self._bucket_suffix

    def rebuild_bucket(self, bucket_name):
        """TODO: 清空、删除并新建cos桶"""
        pass
