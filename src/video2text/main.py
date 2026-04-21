"""PyQt6 application entry point."""
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from video2text.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Video2Text")

    try:
        window = MainWindow()
        window.show()
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", str(e))
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
