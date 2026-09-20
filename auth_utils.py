"""Xác thực người dùng: hash mật khẩu, load/save users."""
import hashlib
import secrets
import json
import os
import re

USERS_FILE = "users.json"
REMEMBER_FILE = "remember_me.json"


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, digest


def verify_password(password, salt, stored_hash):
    _, digest = hash_password(password, salt)
    return digest == stored_hash


def is_valid_email(s):
    # cho phép email hoặc số điện thoại
    if re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s):
        return True
    if re.fullmatch(r"0[0-9]{9,10}", s):
        return True
    return len(s) >= 3

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[users] Không đọc được {USERS_FILE}: {e}")
    return {}


def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[users] Không lưu được {USERS_FILE}: {e}")

