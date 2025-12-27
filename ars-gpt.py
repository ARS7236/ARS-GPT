import sys
from PyQt6.QtWidgets import QApplication
from assets.py.ui.main import ARSGPTMainWindow

def main():
    app = QApplication(sys.argv)
    window = ARSGPTMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
