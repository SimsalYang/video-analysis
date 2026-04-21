"""Main window UI - minimal stub to verify PyQt6 import."""
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video2Text")
        self.setMinimumSize(900, 700)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Video2Text - Loading..."))
        self.setCentralWidget(central)
