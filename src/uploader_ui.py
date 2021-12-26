import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit, QApplication, QLabel, QMessageBox,
    QProgressBar, QFileDialog, QHBoxLayout, QVBoxLayout, QCheckBox, QDialog,
    QComboBox)

from pkg.utils.logger import get_logger
from pkg.utils.qt_utils import reconnect
from src.obsidian import find_ob_imgs, update_ob_file
from src.uploader import Uploader
from src.config_loader import ConfigLoader
from src.img_server_ui import SetupImageServerDialog
from pkg.tencent_cos.cos_bucket import TencentCosBucket


class ObsidianImageUploader(QWidget):
    """上传Obsidian文件到腾讯COS，GUI部分"""

    def __init__(self):
        super().__init__()
        self.log = get_logger(self.__class__.__name__)
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.read_config()
        self.overwrite = False
        self.ob_valut_path = self.config['obsidian']['vault_path']
        self._init_ui()
        self.upload_thread = self._init_upload_thread()
        self.setup_img_dlg = SetupImageServerDialog()
        self.setup_img_dlg.setWindowModality(Qt.ApplicationModal)
        self.setup_img_dlg.config_saved.connect(self.try_connect_img_server)

    def _init_upload_thread(self):
        uploder = Uploader(
            bucket_name=self.config['cos']['tencent']['bucket'],
            local_files=[],
            remote_dir=self.config['cos']['tencent']['dir'] + '/'
        )
        # uploder.start()
        return uploder

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
        self.ob_attachment_path.setText(self.config['obsidian']['attachment_path'])
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
        self.check_result = QLabel('尚未检查过同步状态')
        self.check_sync_status_btn.clicked.connect(self.check_sync_status)
        check_layout.addWidget(self.check_sync_status_btn)
        check_layout.addWidget(self.check_result)
        check_layout.addStretch(1)

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
        self.overwrite_tip_lable = QLabel('        新文件后缀:')
        self.overwrite_suffix = QLineEdit()
        self.overwrite_suffix.setText(self.config['obsidian']['overwrite_suffix'])
        overwrite_layout.addWidget(self.overwrite_checkbox)
        overwrite_layout.addWidget(self.overwrite_tip_lable)
        overwrite_layout.addWidget(self.overwrite_suffix)
        overwrite_layout.addStretch(1)

        self.import_ob_md_btn = QPushButton('选择Obsidian笔记文件')
        self.import_ob_md_btn.clicked.connect(self.import_ob_md_file)
        self.ob_md_file_path = QLineEdit()
        self.ob_md_file_path.setText(self.config['obsidian']['note_default_path'])
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
        self.upload_thread.local_files = os.listdir(self.ob_attachment_path.text())
        reconnect(self.upload_thread.console_log_text, self.update_console)
        reconnect(self.upload_thread.check_result, self.update_check_result)
        self.upload_thread.event_queue.put('CHECK')

    def update_check_result(self, check_result):
        self.check_result.setText(check_result)

    def sync_all_image(self):
        file_names = os.listdir(self.ob_attachment_path.text())
        self.upload_thread.local_files = [os.path.join(self.ob_attachment_path.text(), file)
                                          for file in file_names]
        reconnect(self.upload_thread.console_log_text, self.update_console)
        reconnect(self.upload_thread.upload_progress_max_value, self.update_sync_p_bar_max_value)
        reconnect(self.upload_thread.upload_progress_value, self.update_sync_p_bar_value)
        self.upload_thread.event_queue.put('UPLOAD')

    def update_sync_p_bar_max_value(self, max_value):
        self.sync_progress_bar.setMaximum(max_value)

    def update_sync_p_bar_value(self, value):
        self.sync_progress_bar.setValue(value)

    def import_ob_md_file(self):
        dlg_open_files = QFileDialog()
        current_ledit_path = self.ob_md_file_path.text()
        if os.path.exists(current_ledit_path):
            default_path = current_ledit_path
        else:
            default_path = self.ob_valut_path
        file_name = dlg_open_files.getOpenFileName(self, directory=default_path)[0]
        self.config['obsidian']['note_default_path'] = file_name
        self.config_loader.update_config(self.config)
        if file_name:
            self.ob_md_file_path.setText(file_name)

    def change_ob_attachment_path(self):
        dlg_open_path = QFileDialog()
        path = os.environ['HOME']
        try:
            path = dlg_open_path.getExistingDirectory(caption="选取Obsidian附件", directory=path)
        except Exception as e:
            self.log.error(e)
        self.config['obsidian']['attachment_path'] = path
        self.config_loader.update_config(self.config)
        self.ob_attachment_path.setText(path)

    def start_convert_to_stmd(self):
        self.start_convert_btn.setDisabled(True)
        ob_file = self.ob_md_file_path.text()
        self.log.info(f'Obsidian文件: {ob_file}')
        ob_file_images = find_ob_imgs(ob_file)
        img_root = self.ob_attachment_path.text()
        imgs = [os.path.join(img_root, img) for img in ob_file_images]
        self.upload_thread.local_files = imgs
        reconnect(self.upload_thread.upload_progress_max_value, self.update_convert_p_bar_max_value)
        reconnect(self.upload_thread.upload_progress_value, self.update_convert_p_bar_value)
        reconnect(self.upload_thread.files_url, self.update_ob_file_urls)
        self.upload_thread.event_queue.put('UPLOAD')

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
            self.config['obsidian']['overwrite_suffix'] = suffix
        self.config['obsidian']['recent_not_path'] = self.ob_md_file_path.text()
        self.config_loader.update_config(self.config)
        result, new_ob_file = update_ob_file(ob_file, pure_url_dict, suffix)
        result = '成功' if result is True else '失败'
        self.start_convert_btn.setEnabled(True)
        self.console_textedit.append('-' * 20 + f'更新文件{result}: {new_ob_file}' + '-' * 20)

    def need_overwrite(self):
        self.overwrite = self.overwrite_checkbox.checkState() == Qt.Checked
        self.log.warning(f'overwrite: {self.overwrite}')
        if self.overwrite is True:
            self.overwrite_tip_lable.setDisabled(True)
            self.overwrite_suffix.setDisabled(True)
        else:
            self.overwrite_tip_lable.setEnabled(True)
            self.overwrite_suffix.setEnabled(True)

    def setup_img_server(self):
        self.setup_img_dlg.show()

    def try_connect_img_server(self):
        try:
            self.upload_thread.connect_bucket()
            self.check_img_server_label.setText(
                '已成功连接到图床服务器，同步功能可用')
            self.check_img_server_label.setStyleSheet(
                "QLabel { color : green; }")
            self.enable_all_func_btn()
            self.upload_thread.start()
        except Exception as e:
            self.log.error(f'cannot connect image server, REASON: {str(e)}')
            self.check_img_server_label.setText(
                '无法连接到图床服务器，请检查网络连接或修改图床配置')
            self.check_img_server_label.setStyleSheet(
                "QLabel { color : red; }")
            self.disable_all_func_btn()

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
