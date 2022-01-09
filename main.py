import os
import sys

from PySide6.QtWidgets import QApplication
import qdarktheme

from pkg.utils.better_logger import init_logger
from src.uploader_ui import ObsidianImageUploader

USER_HOME = os.environ['HOME']
APP_NAME = 'ObsidianImageUploader'

if __name__ == '__main__':
    init_logger(os.path.join(USER_HOME, 'Library/Logs', APP_NAME))
    app = QApplication(sys.argv)
    oiu = ObsidianImageUploader()
    app.setStyleSheet(qdarktheme.load_stylesheet('light'))
    oiu.show()
    oiu.try_connect_img_server()
    sys.exit(app.exec())
