import sys
from PyQt6.QtWidgets import QApplication
from video2text.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
