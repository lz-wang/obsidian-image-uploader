from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QPushButton, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QDialog,
    QComboBox)
from loguru import logger

from pkg.utils.qt_utils import reconnect
from src.config_loader import ConfigLoader
from src.img_server import ImageServer


class SetupImageServerDialog(QDialog):
    config_saved = Signal(bool)

    def __init__(self):
        super().__init__()
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.read_config()
        self.log = logger
        self.img_server = None
        self._init_ui()
        self._init_img_server()

    def _init_ui(self):
        self.label_width = 120
        self.combox_width = 160
        self._init_secret_id_key_ui()
        self._init_connect_ui()
        self._init_close_ui()
        self._init_global_ui()

    def _init_secret_id_key_ui(self):
        secret_id_label = QLabel('腾讯云 SecretId:')
        secret_id_label.setFixedWidth(self.label_width)
        self.secret_id_lineedit = QLineEdit()
        if self.config.cos.tencent.secret_id == 'xxx':
            self.secret_id_lineedit.setPlaceholderText('请配置腾讯云的SecretId')
        self.secret_id_layout = QHBoxLayout()
        self.secret_id_layout.addWidget(secret_id_label)
        self.secret_id_layout.addWidget(self.secret_id_lineedit)

        secret_key_label = QLabel('腾讯云 SecretKey:')
        secret_key_label.setFixedWidth(self.label_width)
        self.secret_key_lineedit = QLineEdit()
        self.secret_key_lineedit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        if self.config.cos.tencent.secret_key == 'xxx':
            self.secret_key_lineedit.setPlaceholderText('请配置腾讯云的SecretKey')
        self.secret_key_layout = QHBoxLayout()
        self.secret_key_layout.addWidget(secret_key_label)
        self.secret_key_layout.addWidget(self.secret_key_lineedit)

    def _init_connect_ui(self):
        self.check_connect_layout = QHBoxLayout()
        connect_status_label = QLabel('腾讯云 连接状态:')
        connect_status_label.setFixedWidth(self.label_width)
        self.check_connect_btn = QPushButton('刷新')
        self.check_connect_btn.clicked.connect(self.check_connect)
        self.check_connect_label = QLabel('尚未测试连接状态')
        self.check_connect_layout.addWidget(connect_status_label)
        self.check_connect_layout.addWidget(self.check_connect_label)
        self.check_connect_layout.addStretch(1)
        self.check_connect_layout.addWidget(self.check_connect_btn)

        default_bucket_label = QLabel('选择默认存储桶:')
        default_bucket_label.setFixedWidth(self.label_width)
        self.select_bucket_box = QComboBox()
        self.select_bucket_box.currentTextChanged.connect(self.select_folder)
        self.select_bucket_box.setMinimumWidth(150)
        self.select_bucket_box.setToolTip('⚠️ 存储桶必须为\"公有读"权限时，才能被公网访问')
        self.config_bucket_label = QLabel()
        default_bucket_layout = QHBoxLayout()
        default_bucket_layout.addWidget(default_bucket_label)
        default_bucket_layout.addWidget(self.select_bucket_box)
        default_bucket_layout.addWidget(self.config_bucket_label)
        default_bucket_layout.addStretch(1)

        default_dir_label = QLabel('选择默认存储目录:')
        default_dir_label.setFixedWidth(self.label_width)
        self.select_dir_box = QComboBox()
        self.select_dir_box.setMinimumWidth(150)
        self.config_dir_label = QLabel()
        default_dir_layout = QHBoxLayout()
        default_dir_layout.addWidget(default_dir_label)
        default_dir_layout.addWidget(self.select_dir_box)
        default_dir_layout.addWidget(self.config_dir_label)
        default_dir_layout.addStretch(1)

        self.select_layout = QVBoxLayout()
        self.select_layout.addLayout(default_bucket_layout)
        self.select_layout.addLayout(default_dir_layout)
        self.select_layout.addStretch(1)

    def _init_close_ui(self):
        self.apply_btn = QPushButton('保存并应用')
        self.apply_btn.clicked.connect(self.apply_changes)
        self.help_apply_layout = QHBoxLayout()
        self.help_apply_layout.addStretch(1)
        self.help_apply_layout.addWidget(self.apply_btn)

    def _init_global_ui(self):
        global_layout = QVBoxLayout()
        global_layout.addLayout(self.secret_id_layout)
        global_layout.addLayout(self.secret_key_layout)
        global_layout.addLayout(self.check_connect_layout)
        global_layout.addLayout(self.select_layout)
        global_layout.addStretch(1)
        global_layout.addLayout(self.help_apply_layout)
        self.setLayout(global_layout)
        self.setWindowTitle('配置图床服务器')
        self.refresh_ui_from_config()
        self.setFixedSize(600, 300)

    def _init_img_server(self):
        self.img_server = ImageServer()
        reconnect(self.img_server.bucket_list, self.set_select_bucket_box)
        reconnect(self.img_server.dir_list, self.set_select_folder_box)
        reconnect(self.img_server.check_result, self.set_check_connect_label)
        reconnect(self.img_server.tip_text, self.set_check_connect_label)
        self.img_server.start()

    def check_connect(self):
        self.save_config_from_ui()
        self.check_connect_label.setText('正在尝试连接到图床服务器，请等待...')
        self.check_connect_label.setStyleSheet("QLabel { color : #42a5f5; }")
        self.img_server.event_queue.put({'type': 'LIST_BUCKET', 'cos': 'tencent'})

    def set_check_connect_label(self, result, info):
        if result is True:
            self.check_connect_label.setText('已成功连接到图床服务器，同步功能可用')
            self.check_connect_label.setStyleSheet("QLabel { color : #66bb6a; }")
        else:
            self.log.error(f'cannot connect image server, REASON: {info}')
            self.check_connect_label.setText('无法连接到图床服务器，请检查网络连接或修改图床配置')
            self.check_connect_label.setStyleSheet("QLabel { color : #ef5350; }")

    def set_select_bucket_box(self, buckets: list):
        self.log.info(f'Receive bucket list: {buckets}')
        self.select_bucket_box.clear()
        if self.config.cos.tencent.bucket in buckets:
            self.select_bucket_box.addItem(self.config.cos.tencent.bucket)
            self.select_bucket_box.setCurrentText(self.config.cos.tencent.bucket)
            buckets.remove(self.config.cos.tencent.bucket)
        else:
            self.log.warning(f'Cannot find bucket {self.config.cos.tencent.bucket}, set default.')
            self.select_bucket_box.setCurrentIndex(0)
        for bucket in buckets:
            self.select_bucket_box.addItem(bucket)

    def select_folder(self):
        bucket_name = self.select_bucket_box.currentText()
        if not bucket_name:
            return
        self.img_server.event_queue.put({'type': 'LIST_FILES', 'bucket': bucket_name})

    def set_select_folder_box(self, dir_list):
        self.select_dir_box.clear()
        for folder in dir_list:
            self.select_dir_box.addItem(folder)
        self.select_dir_box.setCurrentIndex(0)

    def apply_changes(self):
        self.save_config_from_ui()
        self.config_saved.emit(True)
        self.close()

    def save_config_from_ui(self):
        self.config.cos.tencent.secret_id = self.secret_id_lineedit.text()
        self.config.cos.tencent.secret_key = self.secret_key_lineedit.text()
        self.config.cos.tencent.bucket = self.select_bucket_box.currentText()
        self.config.cos.tencent.dir = self.select_dir_box.currentText()
        self.config_loader.update_config(self.config)
        self.log.info('Config Saved Success')

    def refresh_ui_from_config(self):
        self.secret_id_lineedit.setText(self.config.cos.tencent.secret_id)
        self.secret_key_lineedit.setText(self.config.cos.tencent.secret_key)
        self.config_bucket_label.setText(f'(当前配置存储桶: {self.config.cos.tencent.bucket[:15]})')
        self.config_bucket_label.setToolTip(self.config.cos.tencent.bucket)
        self.config_dir_label.setText(f'(当前配置存储目录: {self.config.cos.tencent.dir[:15]})')
        self.config_dir_label.setToolTip(self.config.cos.tencent.dir)
