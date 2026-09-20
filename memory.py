"""Bộ nhớ hội thoại (SmartMemory)."""
import json
import os
import datetime

MEMORY_FILE = "bot_memory.json"


class SmartMemory:
    def __init__(self, max_history=30):
        self.history = []
        self.max_history = max_history

    def add(self, user, ai):
        self.history.append({
            "user": user,
            "ai": ai,
            "time": datetime.datetime.now().strftime("%H:%M")
        })
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def last_topics(self, n=3):
        return [h["user"] for h in self.history[-n:]]

    def save(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SmartMemory] Không lưu được bộ nhớ: {e}")

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"[SmartMemory] Không đọc được bộ nhớ: {e}")


memory = SmartMemory()
memory.load()
