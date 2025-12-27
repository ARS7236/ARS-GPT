from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt

class CrashHandler(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARS-GPT Crash Handler")

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.movie = QMovie("assets/gifs/crash.gif")
        self.gif_label.setMovie(self.movie)

        layout.addWidget(self.gif_label)

        self.movie.start()
        self.hide()

    def show_crash(self, error_msg: str):
        print("Crash detected:", error_msg)
        self.movie.start()
        self.show()

    def hide_crash(self):
        self.movie.stop()
        self.hide()
