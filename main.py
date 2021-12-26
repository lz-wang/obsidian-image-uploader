import sys

from PySide6.QtWidgets import QApplication
import qdarktheme

from src.uploader_ui import ObsidianImageUploader

if __name__ == '__main__':
    app = QApplication(sys.argv)
    oiu = ObsidianImageUploader()
    app.setStyleSheet(qdarktheme.load_stylesheet('light'))
    oiu.show()
    oiu.try_connect_img_server()
    sys.exit(app.exec())

