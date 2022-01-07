from pydantic import BaseModel

DEFAULT_CONFIG = {
    'cos': {
        'tencent': {
            'bucket': 'obsidian',
            'dir': 'obsidian',
            'secret_id': 'xxx',
            'secret_key': 'xxx'
        }
    },
    'obsidian': {
        'attachment_path': '/',
        'note_default_path': '/',
        'overwrite_suffix': '_new',
        'recent_note_path': '/',
        'vault_path': '/'
    }
}


class TencentCosConfigModel(BaseModel):
    bucket: str
    dir: str
    secret_id: str
    secret_key: str


class CosConfigModel(BaseModel):
    tencent: TencentCosConfigModel


class ObsidianConfigModel(BaseModel):
    attachment_path: str
    note_default_path: str
    overwrite_suffix: str
    recent_note_path: str
    vault_path: str


class AppConfigModel(BaseModel):
    cos: CosConfigModel
    obsidian: ObsidianConfigModel
