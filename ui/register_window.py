"""Cửa sổ đăng ký."""
import os
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox

from auth_utils import load_users, save_users, hash_password, is_valid_email

class RegisterWindow(QMainWindow):
    def __init__(self, login_window):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "register_beautiful.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "register_fixed.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "register.ui")
        uic.loadUi(ui_path, self)

        self.login_window = login_window

        # Fix: hỗ trợ cả tên nút cũ và mới
        if hasattr(self, 'btnRegister'):
            self.btnRegister.clicked.connect(self.handle_register)
        if hasattr(self, 'btnSignUp'):
            self.btnSignUp.clicked.connect(self.handle_register)
        if hasattr(self, 'btnGoLogin'):
            self.btnGoLogin.clicked.connect(self.back_to_login)
        if hasattr(self, 'btnLogin') and not hasattr(self, 'btnGoLogin'):
            # nếu UI cũ dùng btnLogin để quay lại
            self.btnLogin.clicked.connect(self.back_to_login)

        # Enter để đăng ký
        if hasattr(self, 'txtPasswordConfirm'):
            self.txtPasswordConfirm.returnPressed.connect(self.handle_register)
        elif hasattr(self, 'txtPassword1'):
            self.txtPassword1.returnPressed.connect(self.handle_register)

    def show_error(self, title, msg):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(msg)
        box.setIcon(QMessageBox.Icon.Warning)
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
        """)
        box.exec()

    def handle_register(self):
        email = self.txtEmail.text().strip()
        pw = self.txtPassword.text()
        # hỗ trợ cả 2 tên ô confirm
        if hasattr(self, 'txtPasswordConfirm'):
            pw2 = self.txtPasswordConfirm.text()
        else:
            pw2 = self.txtPassword1.text()

        if not email or not pw or not pw2:
            self.show_error("Thiếu thông tin", "Vui lòng điền đầy đủ các ô.")
            return
        if not is_valid_email(email):
            self.show_error("Email không hợp lệ", "Vui lòng nhập email đúng định dạng hoặc số điện thoại.")
            return
        if pw != pw2:
            self.show_error("Không khớp", "Mật khẩu xác nhận không khớp.")
            return
        if len(pw) < 6:
            self.show_error("Mật khẩu yếu", "Mật khẩu cần tối thiểu 6 ký tự.")
            return

        users = load_users()
        if email in users:
            self.show_error("Đã tồn tại", "Email/số điện thoại này đã được đăng ký.")
            return

        salt, hashed = hash_password(pw)
        users[email] = {"salt": salt, "hash": hashed}
        save_users(users)

        box = QMessageBox(self)
        box.setWindowTitle("Thành công")
        box.setText("Tạo tài khoản thành công! Mời đăng nhập.")
        box.setIcon(QMessageBox.Icon.Information)
        box.setStyleSheet("""
            QMessageBox { background-color: #1E1E20; }
            QLabel { color: #FFFFFF; font-size: 14px; }
            QPushButton { background-color: #00D4FF; color: #000000; padding: 8px 20px; border-radius: 8px; font-weight: 700; }
        """)
        box.exec()
        self.back_to_login()

    def back_to_login(self):
        self.login_window.show()
        self.close()
