import sys

from PyQt5.QtWidgets import QApplication

from src.uploader_ui import ObsidianImageUploader

if __name__ == '__main__':
    app = QApplication(sys.argv)
    oiu = ObsidianImageUploader()
    oiu.show()
    oiu.try_connect_img_server()
    sys.exit(app.exec_())

