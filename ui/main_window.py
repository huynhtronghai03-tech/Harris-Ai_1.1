"""Cửa sổ chat chính (AiBotGUI)."""
import html
import datetime
import os
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QMainWindow, QMessageBox, QMenu, QTextEdit, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QAction, QActionGroup

from config import L, LANGUAGES, CURRENT_LANGUAGE, save_language_setting, BOT_NAME
import config
from memory import memory
from services.ai_core import format_message_html, is_image_request, drawing_text
from workers import AIWorker, TranslateHistoryWorker
from moderation import contains_banned_content  # if needed

class AiBotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main_fixed.ui")
        uic.loadUi(ui_path, self)

        self.setWindowTitle(BOT_NAME + " - AI Assistant")
        # Fix font for chat display
        self.chatDisplay.setFont(QFont("Consolas", 12))
        self.chatDisplay.setReadOnly(True)

        # Connect signals - new objectNames
        self.btnSend.clicked.connect(self.send_message)
        self.btnClear.clicked.connect(self.clear_chat)
        self.btnSave.clicked.connect(self.save_chat)
        self.btnSettings.clicked.connect(self.open_settings_menu)

        # Update header text with bot name
        self.lblHeader.setText(f"🤖 {BOT_NAME}")

        # Load language texts
        self.inputBox.setPlaceholderText(L()["placeholder"])
        self.btnSend.setText(L()["send"])
        self.btnClear.setText(L()["clear"])
        self.btnSave.setText(L()["save"])

        self.add_greeting()
        self.inputBox.installEventFilter(self)
        self.inputBox.setFocus()

    def open_settings_menu(self):
        menu = QMenu(self)
        title_action = QAction(L()["settings_menu_title"], self)
        title_action.setEnabled(False)
        menu.addAction(title_action)
        menu.addSeparator()

        group = QActionGroup(self)
        group.setExclusive(True)
        for code, cfg in LANGUAGES.items():
            action = QAction(cfg["label"], self, checkable=True)
            action.setChecked(code == config.CURRENT_LANGUAGE)
            action.triggered.connect(lambda checked, c=code: self.change_language(c))
            group.addAction(action)
            menu.addAction(action)

        menu.addSeparator()
        logout_action = QAction(L()["logout"], self)
        logout_action.triggered.connect(self.confirm_logout)
        menu.addAction(logout_action)

        menu.exec(self.btnSettings.mapToGlobal(self.btnSettings.rect().bottomRight()))

    def confirm_logout(self):
        reply = QMessageBox.question(
            self,
            L()["logout_confirm_title"],
            L()["logout_confirm_message"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout()

    def logout(self):
        memory.save()
        from ui.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def change_language(self, lang_code):
        if lang_code == config.CURRENT_LANGUAGE or lang_code not in LANGUAGES:
            return
        config.CURRENT_LANGUAGE = lang_code
        save_language_setting(lang_code)

        self.inputBox.setPlaceholderText(L()["placeholder"])
        self.btnSend.setText(L()["send"])
        self.btnClear.setText(L()["clear"])
        self.btnSave.setText(L()["save"])

        if not memory.history:
            self.rebuild_chat_display()
            return

        self.btnSettings.setEnabled(False)
        self.inputBox.setEnabled(False)
        self.btnSend.setEnabled(False)
        self.rebuild_chat_display(extra_note=L()["translating"])

        self.translate_worker = TranslateHistoryWorker(memory.history, L()["label"])
        self.translate_worker.finished.connect(self.on_history_translated)
        self.translate_worker.start()

    def on_history_translated(self, translated_history):
        memory.history = translated_history
        self.rebuild_chat_display()
        self.add_message("AI", L()["language_changed"](L()["label"]))
        self.btnSettings.setEnabled(True)
        self.inputBox.setEnabled(True)
        self.btnSend.setEnabled(True)
        self.inputBox.setFocus()

    def rebuild_chat_display(self, extra_note=None):
        self.chatDisplay.clear()
        self.add_greeting()
        for turn in memory.history:
            self.add_message("You", turn["user"])
            self.add_message("AI", turn["ai"])
        if extra_note:
            self.add_message("AI", extra_note)

    def eventFilter(self, obj, event):
        if obj == self.inputBox and event.type() == event.Type.KeyPress:
            is_enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            shift_pressed = (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) == Qt.KeyboardModifier.ShiftModifier
            if is_enter and not shift_pressed:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    time = datetime.datetime.now().strftime("%H:%M")
    def add_message(self, sender, text):
        time = datetime.datetime.now().strftime("%H:%M")
        is_ai = sender == "AI"
        accent = "#00ff88" if is_ai else "#88ccff"
        bg = "#161d19" if is_ai else "#131822"
        name = BOT_NAME if is_ai else L()["you"]
        formatted = format_message_html(text)
        block = (
            f'<div style="margin:10px 4px; padding:10px 14px; '
            f'background-color:{bg}; border-left:3px solid {accent}; border-radius:6px;">'
            f'<div style="color:{accent}; font-weight:bold; font-size:13px; margin-bottom:5px;">'
            f'{name} <span style="color:#777; font-weight:normal;">[{time}]</span></div>'
            f'<div style="color:#e0e0e0; line-height:1.6;">{formatted}</div>'
            f'</div>'
        )
        self.chatDisplay.append(block)
        self.chatDisplay.verticalScrollBar().setValue(self.chatDisplay.verticalScrollBar().maximum())

    def add_image_message(self, image_path, caption):
        time = datetime.datetime.now().strftime("%H:%M")
        abs_path = os.path.abspath(image_path).replace("\\", "/")
        if not abs_path.startswith("/"):
            abs_path = "/" + abs_path
        formatted_caption = format_message_html(caption)
        block = (
            f'<div style="margin:10px 4px; padding:10px 14px; '
            f'background-color:#161d19; border-left:3px solid #00ff88; border-radius:6px;">'
            f'<div style="color:#00ff88; font-weight:bold; font-size:13px; margin-bottom:5px;">'
            f'{BOT_NAME} <span style="color:#777; font-weight:normal;">[{time}]</span></div>'
            f'<div style="color:#e0e0e0; line-height:1.6; margin-bottom:8px;">{formatted_caption}</div>'
            f'<img src="file://{abs_path}" width="480">'
            f'</div>'
        )
        self.chatDisplay.append(block)
        self.chatDisplay.verticalScrollBar().setValue(self.chatDisplay.verticalScrollBar().maximum())

    def add_greeting(self):
        block = (
            '<div style="margin:10px 4px; padding:10px 14px; '
            'background-color:#1c1522; border-left:3px solid #ff88ff; border-radius:6px;">'
            f'<div style="color:#ff88ff; font-weight:bold; font-size:13px; margin-bottom:5px;">{BOT_NAME}</div>'
            f'<div style="color:#e0e0e0; line-height:1.6;">{html.escape(L()["greeting"])}</div>'
            '</div>'
        )
        self.chatDisplay.append(block)

    def send_message(self):
        text = self.inputBox.toPlainText().strip()
        if not text:
            return

        self.add_message("You", text)
        self.inputBox.clear()
        self.inputBox.setEnabled(False)

        cursor = self.chatDisplay.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.thinking_pos = cursor.position()

        status_label = drawing_text() if is_image_request(text) else L()["thinking"]
        self.chatDisplay.append(
            f'<div style="margin:6px 4px; color:#ffaa00;"><i>{html.escape(status_label)}</i></div>'
        )

        self.worker = AIWorker(text)
        self.worker.finished.connect(self.on_response_ready)
        self.worker.start()

    def on_response_ready(self, user_text, response):
        cursor = self.chatDisplay.textCursor()
        cursor.setPosition(self.thinking_pos)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

        image_path = getattr(self.worker, "image_path", None)
        if image_path:
            self.add_image_message(image_path, response)
        else:
            self.add_message("AI", response)
        memory.add(user_text, response)
        self.inputBox.setEnabled(True)
        self.inputBox.setFocus()

    def clear_chat(self):
        self.chatDisplay.clear()
        self.add_greeting()
        memory.history = []

    def save_chat(self):
        try:
            with open("chat_history.txt", "w", encoding="utf-8") as f:
                f.write(self.chatDisplay.toPlainText())
            self.add_message("AI", L()["saved_chat"])
        except Exception as e:
            self.add_message("AI", L()["save_error"](e))

    def closeEvent(self, event):
        memory.save()
        event.accept()
