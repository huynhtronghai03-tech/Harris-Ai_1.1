"""Entry point — chạy app Harris AI."""
import sys
from PyQt6.QtWidgets import QApplication

from ui.login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())