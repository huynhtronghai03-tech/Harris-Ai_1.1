"""QThread workers: AIWorker, TranslateHistoryWorker."""
from PyQt6.QtCore import QThread, pyqtSignal

from services.ai_core import (
    get_response, translate_text, is_image_request, generate_image,
    image_error_text, image_caption_text, ask_local_ai_stream,
    looks_like_math, WHO_TRIGGERS, TIME_TRIGGERS, SEARCH_TRIGGERS,
)
from moderation import contains_banned_content, content_warning_text
from memory import memory

class AIWorker(QThread):
    finished = pyqtSignal(str, str)
    streaming = pyqtSignal(str)
    def __init__(self, user_text):
        super().__init__()
        self.user_text = user_text
        self._full = ""
        self.image_path = None
    def _on_chunk(self, c):
        self._full += c
        self.streaming.emit(c)
    def run(self):
        try:
            if contains_banned_content(self.user_text):
                self._full = content_warning_text()
                self.streaming.emit(self._full)
                self.finished.emit(self.user_text, self._full)
                return
            t = self.user_text.lower().strip()
            if is_image_request(self.user_text):
                path, used_prompt = generate_image(self.user_text)
                if path == "BLOCKED":
                    self._full = content_warning_text()
                elif path:
                    self.image_path = path
                    self._full = image_caption_text(used_prompt)
                else:
                    self._full = image_error_text()
                self.streaming.emit(self._full)
                self.finished.emit(self.user_text, self._full)
                return
            if any(x in t for x in WHO_TRIGGERS) or any(x in t for x in TIME_TRIGGERS) or looks_like_math(self.user_text):
                resp = get_response(self.user_text)
                self._full = resp
                for i in range(0, len(resp), 20):
                    self.streaming.emit(resp[i:i+20])
            elif any(x in t for x in SEARCH_TRIGGERS):
                resp = get_response(self.user_text)
                self._full = resp
                self.streaming.emit(resp)
            else:
                resp = ask_local_ai_stream(self.user_text, memory.history, self._on_chunk)
                self._full = resp
        except Exception as e:
            self._full = f"Lỗi: {e}"
            self.streaming.emit(self._full)
        self.finished.emit(self.user_text, self._full)


class TranslateHistoryWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, history, target_label):
        super().__init__()
        self.history = [dict(turn) for turn in history]
        self.target_label = target_label

    def run(self):
        for turn in self.history:
            turn["ai"] = translate_text(turn["ai"], self.target_label)
        self.finished.emit(self.history)
