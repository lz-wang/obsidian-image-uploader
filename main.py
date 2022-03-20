import os
import sys

from PySide6.QtWidgets import QApplication
import qdarktheme

from pkg.utils.better_logger import init_logger
from src.uploader_ui import ObsidianImageUploader
from src.env import USER_HOME, APP_NAME, show_env


if __name__ == '__main__':
    show_env()
    init_logger(os.path.join(USER_HOME, APP_NAME, 'logs'))
    app = QApplication(sys.argv)
    oiu = ObsidianImageUploader()
    app.setStyleSheet(qdarktheme.load_stylesheet('light'))
    oiu.show()
    oiu.try_connect_img_server()
    sys.exit(app.exec())
