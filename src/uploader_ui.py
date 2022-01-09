import os
import sys
import traceback

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit, QApplication, QLabel,
    QProgressBar, QFileDialog, QHBoxLayout, QVBoxLayout, QCheckBox)
from loguru import logger as log

from pkg.tencent_cos.exceptions import CosBucketNotFoundError, CosBucketDirNotFoundError
from pkg.utils.qt_utils import reconnect, set_label_text
from src.config_loader import ConfigLoader
from src.img_server_ui import SetupImageServerDialog
from src.obsidian import find_ob_imgs, update_ob_file
from src.uploader import Uploader


class ObsidianImageUploader(QWidget):
    """上传Obsidian文件到腾讯COS，GUI部分"""

    def __init__(self):
        super().__init__()
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.read_config()
        self.overwrite = False
        self.ob_valut_path = self.config.obsidian.vault_path
        self._init_ui()
        self._init_upload_thread()
        self.setup_img_dlg = SetupImageServerDialog()
        self.setup_img_dlg.setWindowModality(Qt.ApplicationModal)
        self.setup_img_dlg.config_saved.connect(self.try_connect_img_server)

    def _init_upload_thread(self):
        self.upload_thread = QThread()
        self.upload_worker = Uploader()
        self.upload_worker.moveToThread(self.upload_thread)
        reconnect(self.upload_worker.check_result, self.update_check_result)
        reconnect(self.upload_worker.upload_progress_max_value, self.update_sync_p_bar_max_value)
        reconnect(self.upload_worker.upload_progress_value, self.update_sync_p_bar_value)

    def _init_ui(self):
        self._init_attachment_ui()
        self._init_check_sync_ui()
        self._init_convert_ui()
        self._init_console_ui()
        self._init_global_layout()

    def _init_attachment_ui(self):
        self.prepare_attachment_label = QLabel('准备工作：')
        # 设置图床
        self.setup_img_server_btn = QPushButton('配置图床服务器')
        self.setup_img_server_btn.clicked.connect(self.setup_img_server)
        self.check_img_server_label = QLabel('正在检测图床连接状态...')

        img_server_layout = QHBoxLayout()
        img_server_layout.addWidget(self.setup_img_server_btn)
        img_server_layout.addWidget(self.check_img_server_label)
        img_server_layout.addStretch(1)

        # 设置Obsidian附件路径
        self.change_attachment_btn = QPushButton('配置Obsidian附件路径')
        self.change_attachment_btn.clicked.connect(self.change_ob_attachment_path)
        self.ob_attachment_path = QLineEdit()
        self.ob_attachment_path.setText(self.config.obsidian.attachment_path)
        attachment_selecter_layout = QHBoxLayout()
        attachment_selecter_layout.addWidget(self.change_attachment_btn)
        attachment_selecter_layout.addWidget(self.ob_attachment_path)

        self.prepare_layout = QVBoxLayout()
        self.prepare_layout.addWidget(self.prepare_attachment_label)
        self.prepare_layout.addLayout(img_server_layout)
        self.prepare_layout.addLayout(attachment_selecter_layout)

    def _init_check_sync_ui(self):
        self.func_1_label = QLabel('功能1：同步所有Obsidian图片到图床')
        check_layout = QHBoxLayout()
        self.check_sync_status_btn = QPushButton('检查同步状态')
        self.check_result_label = QLabel('尚未检查过同步状态')
        self.check_sync_status_btn.clicked.connect(self.check_sync_status)
        self.enable_md5_check_checkbox = QCheckBox('检查文件完整性')
        self.enable_md5_check_checkbox.setToolTip(
            '如果开启此项:\n'
            '(1)将耗费较多流量且检查同步速度下降\n'
            '(2)同步时默认覆盖文件名一致但完整性校验失败的文件')
        self.enable_md5_check_checkbox.setChecked(Qt.CheckState.Unchecked)
        self.enable_md5_check_checkbox.stateChanged.connect(self.show_md5_check_status)
        check_layout.addWidget(self.check_sync_status_btn)
        check_layout.addWidget(self.check_result_label)
        check_layout.addStretch(1)
        check_layout.addWidget(self.enable_md5_check_checkbox)

        sync_layout = QHBoxLayout()
        self.sync_all_images_btn = QPushButton('同步附件图片')
        self.sync_all_images_btn.clicked.connect(self.sync_all_image)
        self.sync_progress_bar = QProgressBar()
        sync_layout.addWidget(self.sync_all_images_btn)
        sync_layout.addWidget(self.sync_progress_bar)

        self.check_sync_layout = QVBoxLayout()
        self.check_sync_layout.addWidget(self.func_1_label)
        self.check_sync_layout.addLayout(check_layout)
        self.check_sync_layout.addLayout(sync_layout)

    def _init_convert_ui(self):
        self.func_2_label = QLabel('功能2：将单个Obsidian笔记文件图片链接转换为标准形式')

        overwrite_layout = QHBoxLayout()
        self.overwrite_checkbox = QCheckBox('覆盖原始Obsidian文件')
        self.overwrite_checkbox.stateChanged.connect(self.need_overwrite)
        self.overwrite_checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.overwrite_tip_label = QLabel('        新文件后缀:')
        self.overwrite_suffix = QLineEdit()
        self.overwrite_suffix.setText(self.config.obsidian.overwrite_suffix)
        overwrite_layout.addWidget(self.overwrite_checkbox)
        overwrite_layout.addWidget(self.overwrite_tip_label)
        overwrite_layout.addWidget(self.overwrite_suffix)
        overwrite_layout.addStretch(1)

        self.import_ob_md_btn = QPushButton('选择Obsidian笔记文件')
        self.import_ob_md_btn.clicked.connect(self.import_ob_md_file)
        self.ob_md_file_path = QLineEdit()
        self.ob_md_file_path.setText(self.config.obsidian.note_default_path)
        md_file_layout = QHBoxLayout()
        md_file_layout.addWidget(self.import_ob_md_btn)
        md_file_layout.addWidget(self.ob_md_file_path)

        self.start_convert_btn = QPushButton('开始转换Obsidian笔记')
        self.start_convert_btn.clicked.connect(self.start_convert_to_stmd)
        self.convert_progressbar = QProgressBar()
        c2_layout = QHBoxLayout()
        c2_layout.addWidget(self.start_convert_btn)
        c2_layout.addWidget(self.convert_progressbar)

        self.convert_layout = QVBoxLayout()
        self.convert_layout.addWidget(self.func_2_label)
        self.convert_layout.addLayout(overwrite_layout)
        self.convert_layout.addLayout(md_file_layout)
        self.convert_layout.addLayout(c2_layout)

    def _init_console_ui(self):
        self.console_textedit = QTextEdit()
        self.console_textedit.setPlaceholderText('当前程序的运行log将在此显示')

    def _init_global_layout(self):
        global_layout = QVBoxLayout()
        global_layout.addLayout(self.prepare_layout)
        global_layout.addLayout(self.check_sync_layout)
        global_layout.addLayout(self.convert_layout)
        global_layout.addStretch(1)
        global_layout.addWidget(self.console_textedit)
        self.setLayout(global_layout)
        self.setFixedSize(1000, 600)
        self.setWindowTitle('Obsidian图片工具箱')

    def check_sync_status(self):
        self.reset_upload_params()
        reconnect(self.upload_thread.started, self.upload_worker.check_files)
        reconnect(self.upload_worker.check_finished, self.upload_thread.quit)
        self.disable_sync_btns_until_finished()
        self.check_result_label.setText('正在检查同步状态...')
        self.console_textedit.append('='*80)
        self.upload_thread.start()

    def update_check_result(self, check_result: str):
        self.check_result_label.setText(str(check_result))

    def disable_sync_btns_until_finished(self):
        self.check_sync_status_btn.setEnabled(False)
        self.sync_all_images_btn.setEnabled(False)
        reconnect(self.upload_thread.finished,
                  [lambda: self.check_sync_status_btn.setEnabled(True),
                   lambda: self.sync_all_images_btn.setEnabled(True)])

    def sync_all_image(self):
        self.reset_upload_params()
        reconnect(self.upload_thread.started, self.upload_worker.upload_files)
        reconnect(self.upload_worker.upload_finished, self.upload_thread.quit)
        self.disable_sync_btns_until_finished()
        self.upload_thread.start()

    def reset_upload_params(self):
        file_names = os.listdir(self.ob_attachment_path.text())
        self.upload_worker.local_files = [os.path.join(self.ob_attachment_path.text(), file)
                                          for file in file_names]
        self.upload_worker.check_md5 = self.enable_md5_check_checkbox.isChecked()
        reconnect(self.upload_worker.console_log_text, self.update_console)

    def update_sync_p_bar_max_value(self, max_value):
        self.sync_progress_bar.setMaximum(max_value)

    def update_sync_p_bar_value(self, value):
        self.sync_progress_bar.setValue(value)

    def import_ob_md_file(self):
        dlg_open_files = QFileDialog()
        if os.path.exists(self.ob_md_file_path.text()):
            cur_file_path = self.ob_md_file_path.text()
        else:
            cur_file_path = os.environ['HOME']
        new_file_path = ''
        try:
            new_file_path = dlg_open_files.getOpenFileName(self, dir=cur_file_path)[0]
        except Exception as e:
            log.error(e)
            log.error(traceback.format_exc())
        finally:
            if not os.path.exists(str(new_file_path)):
                new_file_path = cur_file_path
        self.config.obsidian.note_default_path = new_file_path
        self.config_loader.update_config(self.config)
        if new_file_path:
            self.ob_md_file_path.setText(new_file_path)

    def change_ob_attachment_path(self):
        if os.path.exists(self.ob_attachment_path.text()):
            cur_path = self.ob_attachment_path.text()
        else:
            cur_path = os.environ['HOME']
        dlg_open_path = QFileDialog()
        new_path = ''
        try:
            new_path = dlg_open_path.getExistingDirectory(
                caption="选取Obsidian附件", dir=cur_path)
        except Exception as e:
            log.error(e)
            log.error(traceback.format_exc())
        finally:
            if not new_path:
                new_path = cur_path
        self.config.obsidian.attachment_path = new_path
        self.config_loader.update_config(self.config)
        self.ob_attachment_path.setText(new_path)

    def start_convert_to_stmd(self):
        self.start_convert_btn.setDisabled(True)
        ob_file = self.ob_md_file_path.text()
        log.info(f'Obsidian文件: {ob_file}')
        ob_file_images = find_ob_imgs(ob_file)
        img_root = self.ob_attachment_path.text()
        self.upload_worker.local_files = [os.path.join(img_root, img) for img in ob_file_images]
        reconnect(self.upload_worker.upload_progress_max_value, self.update_convert_p_bar_max_value)
        reconnect(self.upload_worker.upload_progress_value, self.update_convert_p_bar_value)
        reconnect(self.upload_worker.files_url, self.update_ob_file_urls)
        self.upload_worker.event_queue.put('UPLOAD')

    def update_convert_p_bar_max_value(self, max_value):
        self.convert_progressbar.setMaximum(max_value)

    def update_convert_p_bar_value(self, i):
        self.convert_progressbar.setValue(i)

    def update_console(self, log_msg):
        self.console_textedit.append(log_msg)

    def update_ob_file_urls(self, url_dict):
        ob_file = self.ob_md_file_path.text()
        pure_url_dict = {}
        for file_path, file_url in url_dict.items():
            file_name = file_path.split('/')[-1]
            pure_url_dict[file_name] = file_url
        if self.overwrite is True:
            suffix = ''
        else:
            suffix = self.overwrite_suffix.text()
            self.config.obsidian.overwrite_suffix = suffix
        self.config.obsidian.recent_note_path = self.ob_md_file_path.text()
        self.config_loader.update_config(self.config)
        result, new_ob_file = update_ob_file(ob_file, pure_url_dict, suffix)
        result = '成功' if result is True else '失败'
        self.start_convert_btn.setEnabled(True)
        self.console_textedit.append('-' * 20 + f'更新文件{result}: {new_ob_file}' + '-' * 20)

    def need_overwrite(self):
        self.overwrite = self.overwrite_checkbox.checkState() == Qt.Checked
        log.warning(f'overwrite: {self.overwrite}')
        if self.overwrite is True:
            self.overwrite_tip_label.setDisabled(True)
            self.overwrite_suffix.setDisabled(True)
        else:
            self.overwrite_tip_label.setEnabled(True)
            self.overwrite_suffix.setEnabled(True)

    def setup_img_server(self):
        self.setup_img_dlg.show()
        self.setup_img_dlg.refresh_ui_from_config()
        self.setup_img_dlg.check_connect()

    def try_connect_img_server(self):
        try:
            self.config = self.config_loader.read_config()
            set_label_text(self.check_img_server_label,
                           '正在尝试连接到图床服务器，请等待...')
            self.upload_worker.connect_bucket_dir()
            set_label_text(self.check_img_server_label,
                           f'已成功连接到图床服务器，同步功能可用 '
                           f'(存储桶: {self.config.cos.tencent.bucket}, '
                           f'文件夹{self.config.cos.tencent.dir})', 'SUCCESS')
            self.enable_all_func_btn()
        except Exception as e:
            log.error(f'cannot connect image server, REASON: {str(e)}')
            log.error(traceback.format_exc())
            if isinstance(e, CosBucketNotFoundError):
                msg = f'网络正常，但无法在图床服务器找到存储桶\"{self.config.cos.tencent.bucket}\"，' \
                      f'请修改图床配置'
            elif isinstance(e, CosBucketDirNotFoundError):
                msg = f'网络正常，但无法在图床服务器存储桶\"{self.config.cos.tencent.bucket}\"' \
                      f'中找到文件夹\"{self.config.cos.tencent.dir}\"，请修改图床配置'
            else:
                msg = '无法连接到图床服务器，请检查网络连接或修改图床服务器配置'
            set_label_text(self.check_img_server_label, msg, 'FAIL')
            self.disable_all_func_btn()

    def show_md5_check_status(self):
        check_status = self.enable_md5_check_checkbox.isChecked()
        log.warning(f'enable md5 check: {check_status}')
        if isinstance(self.upload_worker, Uploader):
            self.upload_worker.check_md5 = check_status

    def disable_all_func_btn(self):
        self.check_sync_status_btn.setDisabled(True)
        self.sync_all_images_btn.setDisabled(True)
        self.start_convert_btn.setDisabled(True)

    def enable_all_func_btn(self):
        self.check_sync_status_btn.setEnabled(True)
        self.sync_all_images_btn.setEnabled(True)
        self.start_convert_btn.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    oiu = ObsidianImageUploader()
    oiu.show()
    sys.exit(app.exec_())
