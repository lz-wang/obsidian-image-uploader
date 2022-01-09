from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QPushButton, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QDialog,
    QComboBox)
from loguru import logger as log

from pkg.utils.qt_utils import reconnect, set_label_text, better_emit
from src.config_loader import ConfigLoader
from src.img_server import ImageServer


class SetupImageServerDialog(QDialog):
    config_saved = Signal()

    def __init__(self):
        super().__init__()
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.read_config()
        self._bucket_worker = None
        self._init_ui()
        self._init_thread_workers()

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
        self.recheck_connect_btn = QPushButton('刷新')
        self.recheck_connect_btn.clicked.connect(self.recheck_connect)
        self.check_connect_label = QLabel('尚未测试连接状态')
        self.check_connect_layout.addWidget(connect_status_label)
        self.check_connect_layout.addWidget(self.check_connect_label)
        self.check_connect_layout.addStretch(1)
        self.check_connect_layout.addWidget(self.recheck_connect_btn)

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

    def _init_thread_workers(self):
        # bucket worker
        self._bucket_thread = QThread()
        self._bucket_worker = ImageServer()
        self._bucket_worker.moveToThread(self._bucket_thread)
        reconnect(self._bucket_thread.started, self._bucket_worker.list_bucket)
        reconnect(self._bucket_worker.check_buckets_finished, self._bucket_thread.quit)
        reconnect(self._bucket_worker.bucket_list, self.set_select_bucket_box)
        reconnect(self._bucket_worker.check_result, self.set_check_connect_label)
        # dir worker
        self._dir_thread = QThread()
        self._dir_worker = ImageServer()
        self._dir_worker.moveToThread(self._dir_thread)
        reconnect(self._dir_worker.check_dirs_finished, self._dir_thread.quit)
        reconnect(self._dir_worker.dir_list, self.set_select_folder_box)

    def check_connect(self):
        self._bucket_thread.start()
        set_label_text(self.check_connect_label, '正在尝试连接到图床服务器，请等待...')

    def recheck_connect(self):
        self.save_config_from_ui()
        self.check_connect()

    def set_check_connect_label(self, result, info):
        if result is True:
            set_label_text(self.check_connect_label,
                           '已成功连接到图床服务器，同步功能可用', 'SUCCESS')
        else:
            log.error(f'cannot connect image server, REASON: {info}')
            set_label_text(self.check_connect_label,
                           '无法连接到图床服务器，请检查网络连接或修改图床配置', 'FAIL')

    def set_select_bucket_box(self, buckets: list):
        log.info(f'Receive bucket list: {buckets}')
        self.select_bucket_box.clear()
        if self.config.cos.tencent.bucket in buckets:
            self.select_bucket_box.addItem(self.config.cos.tencent.bucket)
            self.select_bucket_box.setCurrentText(self.config.cos.tencent.bucket)
            buckets.remove(self.config.cos.tencent.bucket)
        else:
            log.warning(f'Cannot find bucket {self.config.cos.tencent.bucket}, set default.')
            self.select_bucket_box.setCurrentIndex(0)
        self.select_bucket_box.addItems(buckets)

    def select_folder(self):
        reconnect(self._dir_thread.started,
                  lambda: self._dir_worker.list_dirs(self.select_bucket_box.currentText()))
        self._dir_thread.start()

    def set_select_folder_box(self, dir_list):
        self.select_dir_box.clear()
        log.info(f'Receive bucket {self.select_bucket_box.currentText()} dirs: {dir_list}')
        self.select_dir_box.addItems(dir_list)
        self.select_dir_box.setCurrentIndex(0)

    def apply_changes(self):
        self.close()
        self.save_config_from_ui()
        better_emit(self.config_saved)

    def save_config_from_ui(self):
        self.config.cos.tencent.secret_id = self.secret_id_lineedit.text()
        self.config.cos.tencent.secret_key = self.secret_key_lineedit.text()
        self.config.cos.tencent.bucket = self.select_bucket_box.currentText()
        self.config.cos.tencent.dir = self.select_dir_box.currentText()
        self.config_loader.update_config(self.config)
        log.info('Config Saved Success')

    def refresh_ui_from_config(self):
        self.secret_id_lineedit.setText(self.config.cos.tencent.secret_id)
        self.secret_key_lineedit.setText(self.config.cos.tencent.secret_key)
        self.config_bucket_label.setText(f'(当前配置存储桶: {self.config.cos.tencent.bucket[:15]})')
        self.config_bucket_label.setToolTip(self.config.cos.tencent.bucket)
        self.config_dir_label.setText(f'(当前配置存储目录: {self.config.cos.tencent.dir[:15]})')
        self.config_dir_label.setToolTip(self.config.cos.tencent.dir)
