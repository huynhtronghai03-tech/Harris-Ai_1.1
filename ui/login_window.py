"""Cửa sổ đăng nhập."""
import os
import json
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

from auth_utils import load_users, verify_password, is_valid_email, REMEMBER_FILE

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "login_beautiful.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "login_fixed.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "login.ui")
        uic.loadUi(ui_path, self)

        self.register_window = None
        self.chat_window = None

        # Fix: hỗ trợ cả tên nút cũ và mới để không crash
        if hasattr(self, 'btnLogin'):
            self.btnLogin.clicked.connect(self.handle_login)
        if hasattr(self, 'btnGoRegister'):
            self.btnGoRegister.clicked.connect(self.open_register)
        # fallback tên cũ
        if hasattr(self, 'btnRegister') and not hasattr(self, 'btnGoRegister'):
            self.btnRegister.clicked.connect(self.open_register)

        if hasattr(self, 'txtPassword'):
            self.txtPassword.returnPressed.connect(self.handle_login)

        self._load_remembered_email()
        # Fix QMessageBox readability - apply global style
        self._apply_messagebox_style()

    def _apply_messagebox_style(self):
        # Force QMessageBox readable
        self.setStyleSheet(self.styleSheet() + """
            QMessageBox { background-color: #151517; }
            QMessageBox QLabel { color: #FFFFFF; font-size: 14px; background: transparent; }
            QMessageBox QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border-radius: 8px;
                padding: 8px 24px;
                min-width: 80px;
                font-weight: 700;
            }
            QMessageBox QPushButton:hover { background-color: #E0E0E0; }
        """)

    def _load_remembered_email(self):
        if os.path.exists(REMEMBER_FILE):
            try:
                with open(REMEMBER_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.txtEmail.setText(data.get("email", ""))
                if hasattr(self, 'ckSave'):
                    self.ckSave.setChecked(True)
            except Exception as e:
                print(f"[remember_me] Lỗi đọc: {e}")

    def handle_login(self):
        email = self.txtEmail.text().strip()
        password = self.txtPassword.text()

        if not email or not password:
            self.show_error("Thiếu thông tin", "Vui lòng nhập đầy đủ email/số điện thoại và mật khẩu.")
            return
        if not is_valid_email(email):
            self.show_error("Email không hợp lệ", "Vui lòng kiểm tra lại email/số điện thoại.")
            return

        users = load_users()
        user = users.get(email)
        if not user or not verify_password(password, user["salt"], user["hash"]):
            self.show_error("Đăng nhập thất bại", "Email hoặc mật khẩu không đúng.")
            return

        try:
            if hasattr(self, 'ckSave') and self.ckSave.isChecked():
                with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
                    json.dump({"email": email}, f)
            elif os.path.exists(REMEMBER_FILE):
                os.remove(REMEMBER_FILE)
        except Exception as e:
            print(f"[remember_me] Lỗi lưu: {e}")

        self.open_chat()

    def show_error(self, title, msg):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(msg)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setStyleSheet("""
            QMessageBox { background-color: #1E1E20; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                padding: 8px 20px;
                border-radius: 8px;
                font-weight: 700;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #E0E0E0; }
        """)
        box.exec()

    def open_register(self):
        try:
            from ui.register_window import RegisterWindow
            self.register_window = RegisterWindow(self)
            self.register_window.show()
            self.hide()
        except Exception as e:
            print(f"[open_register] Lỗi: {e}")
            import traceback; traceback.print_exc()
            self.show_error("Lỗi", f"Không mở được trang đăng ký: {e}")

    def open_chat(self):
        from ui.main_window import AiBotGUI
        self.chat_window = AiBotGUI()
        self.chat_window.show()
        self.close()
