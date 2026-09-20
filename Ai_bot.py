import sys
import random
import datetime
import json
import os
import re
import html
import hashlib
import secrets
import requests
from urllib.parse import quote
from ddgs import DDGS
import sympy as sp
import ollama
from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton,
                           QVBoxLayout, QHBoxLayout, QWidget, QLabel, QMessageBox,
                           QMenu)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QAction, QActionGroup

BOT_NAME = "Harris"
# ===== CẤU HÌNH NHANH =====
# Đổi model ở đây để tối ưu tốc độ:
# - "llama3.2:1b"  -> nhanh nhất, nhẹ nhất (~1.3GB), trả lời ngắn gọn
# - "qwen2.5:1.5b" -> cân bằng tốc độ + chất lượng, tiếng Việt tốt
# - "llama3.2"     -> chất lượng cao nhất nhưng chậm hơn
# Chạy: ollama pull <tên model> trước khi chạy app

OLLAMA_MODEL = "llama3.2:1b"  # đổi thành "qwen2.5:1.5b" hoặc "llama3.2" nếu muốn mạnh hơn
SETTINGS_FILE = "settings.json"

LANGUAGES = {
    "vi": {
        "label": "Tiếng Việt",
        "system_prompt": (
            f"Bạn là {BOT_NAME}, một trợ lý ảo thân thiện, dí dỏm nhẹ nhàng nhưng lịch sự. "
            "LUÔN LUÔN trả lời bằng tiếng Việt, bất kể người dùng viết bằng ngôn ngữ nào. "
            "Trả lời ngắn gọn, tự nhiên như đang nhắn tin, không chửi thề, "
            "không dài dòng trừ khi người dùng cần giải thích kỹ. "
            "Bạn LUÔN giữ thái độ lịch sự, tôn trọng người dùng. TUYỆT ĐỐI từ chối một cách "
            "nhẹ nhàng nếu người dùng yêu cầu nội dung 18+/khiêu dâm, bạo lực cực đoan, "
            "quấy rối, phân biệt chủng tộc/kỳ thị, hoặc bất kỳ nội dung không phù hợp nào khác. "
            "Bạn thành thạo lập trình với các ngôn ngữ: C, C++, Java, JavaScript, TypeScript, "
            "C#, Go (Golang) và Rust. Khi được yêu cầu viết code, hãy viết code đúng, sạch, "
            "chạy được, luôn đặt trong khối markdown có gắn tên ngôn ngữ "
            "(ví dụ ```cpp ... ```, ```java ... ```, ```go ... ```), và chỉ giải thích ngắn gọn "
            "bên dưới nếu người dùng cần."
        ),
        "greeting": "Xin chào, mình là Harris! Trợ lý cá nhân của bạn. Hỏi mình bất cứ điều gì nhé, Tôi biết tất cả mọi thứ.",
        "thinking": "Đang suy nghĩ...",
        "you": "Bạn",
        "send": "Gửi",
        "clear": "🗑 Xóa chat",
        "save": "💾 Lưu chat",
        "placeholder": "Nhập tin nhắn... (Enter = gửi, Shift+Enter = xuống dòng)",
        "empty_input": "Bạn muốn hỏi gì nào? 🙂",
        "who_are_you": f"Mình là {BOT_NAME} — trợ lý cá nhân của bạn, có thể tính toán, tra cứu và trò chuyện.",
        "no_gender": "Mình là AI thôi, không có giới tính hay xu hướng gì cả 😄",
        "now_is": lambda t, d: f"Bây giờ là **{t}**, ngày **{d}**.",
        "saved_chat": "💾 Đã lưu lịch sử chat vào chat_history.txt",
        "save_error": lambda e: f"⚠️ Không lưu được: {e}",
        "settings_menu_title": "🌐 Ngôn ngữ trả lời",
        "language_changed": lambda name: f"🌐 Đã chuyển ngôn ngữ trả lời sang **{name}**.",
        "translating": "🌐 Đang dịch lại các câu trả lời trước đó, chờ chút nhé...",
        "logout": "🚪 Đăng xuất",
        "logout_confirm_title": "Đăng xuất",
        "logout_confirm_message": "Bạn có chắc muốn đăng xuất không?",
    },
    "en": {
        "label": "English",
        "system_prompt": (
            f"You are {BOT_NAME}, a friendly, lightly witty but polite virtual assistant. "
            "ALWAYS answer in English, no matter what language the user writes in. "
            "Keep replies short and natural, like a chat message, no swearing, "
            "and don't ramble unless the user needs a detailed explanation. "
            "You ALWAYS stay polite and respectful. You POLITELY REFUSE any request for "
            "18+/sexual content, extreme violence, harassment, hate speech/discrimination, "
            "or any other inappropriate content. "
            "You are skilled at programming in C, C++, Java, JavaScript, TypeScript, C#, "
            "Go (Golang), and Rust. When asked to write code, produce correct, clean, "
            "runnable code inside a markdown code block tagged with the language "
            "(e.g. ```cpp ... ```, ```java ... ```, ```go ... ```), and only add a short "
            "explanation below if the user needs one."
        ),
        "greeting": "Hello, I'm Harris! Your personal helper friend. Ask me anything, I know everything.",
        "thinking": "Thinking...",
        "you": "You",
        "send": "Send",
        "clear": "🗑 Clear chat",
        "save": "💾 Save chat",
        "placeholder": "Type a message... (Enter = send, Shift+Enter = new line)",
        "empty_input": "What would you like to ask? 🙂",
        "who_are_you": f"I'm {BOT_NAME} — your personal assistant, I can do math, look things up, and chat.",
        "no_gender": "I'm just an AI, no gender or orientation here 😄",
        "now_is": lambda t, d: f"It's **{t}**, on **{d}**.",
        "saved_chat": "💾 Chat history saved to chat_history.txt",
        "save_error": lambda e: f"⚠️ Couldn't save: {e}",
        "settings_menu_title": "🌐 Reply language",
        "language_changed": lambda name: f"🌐 Reply language switched to **{name}**.",
        "translating": "🌐 Translating previous replies, hold on...",
        "logout": "🚪 Log out",
        "logout_confirm_title": "Log out",
        "logout_confirm_message": "Are you sure you want to log out?",
    },
    "ja": {
        "label": "日本語",
        "system_prompt": (
            f"あなたは{BOT_NAME}という、親しみやすく礼儀正しい、少しユーモアのあるAIアシスタントです。"
            "ユーザーがどの言語で書いても、必ず日本語で返答してください。"
            "返信は短く自然に、チャットのように。下品な言葉は使わず、"
            "ユーザーが詳しい説明を求めない限り長くしないでください。"
            "常に礼儀正しく、相手を尊重してください。18歳以上向け/性的な内容、過激な暴力、"
            "嫌がらせ、差別・ヘイトスピーチ、その他不適切な内容の要求は、丁重に断ってください。"
            "あなたはC、C++、Java、JavaScript、TypeScript、C#、Go（Golang）、Rustでの"
            "プログラミングが得意です。コードを書くよう頼まれたら、正しく動作する"
            "きれいなコードを、言語名を付けたMarkdownのコードブロック（例: ```cpp ... ```、"
            "```java ... ```、```go ... ```）で書いてください。説明はユーザーが求めた場合のみ"
            "簡潔に添えてください。"
        ),
        "greeting": "こんにちは、ハリスです！あなたの個人的なサポーターであり、友達でもあります。何でも聞いてくださいね。何でも知っていますから。",
        "thinking": "考え中...",
        "you": "あなた",
        "send": "送信",
        "clear": "🗑 チャットを削除",
        "save": "💾 チャットを保存",
        "placeholder": "メッセージを入力...（Enter = 送信、Shift+Enter = 改行）",
        "empty_input": "何を聞きたいですか？🙂",
        "who_are_you": f"私は{BOT_NAME}です — 計算、検索、会話ができるあなたの個人アシスタントです。",
        "no_gender": "私はAIなので、性別や性的指向はありません😄",
        "now_is": lambda t, d: f"現在の時刻は **{t}**、日付は **{d}** です。",
        "saved_chat": "💾 チャット履歴を chat_history.txt に保存しました",
        "save_error": lambda e: f"⚠️ 保存できませんでした: {e}",
        "settings_menu_title": "🌐 返信言語",
        "language_changed": lambda name: f"🌐 返信言語を **{name}** に変更しました。",
        "translating": "🌐 これまでの返信を翻訳しています、少々お待ちください...",
        "logout": "🚪 ログアウト",
        "logout_confirm_title": "ログアウト",
        "logout_confirm_message": "本当にログアウトしますか？",
    },
    "ko": {
        "label": "한국어",
        "system_prompt": (
            f"당신은 {BOT_NAME}이라는 친근하고 예의 바르며 약간 재치 있는 AI 비서입니다. "
            "사용자가 어떤 언어로 쓰든 항상 한국어로만 답하세요. "
            "대답은 짧고 자연스럽게, 채팅하듯이 하세요. 욕설은 쓰지 말고, "
            "사용자가 자세한 설명을 원하지 않는 한 길게 늘어놓지 마세요. "
            "항상 예의 바르고 상대방을 존중하세요. 19금/성적인 콘텐츠, 극단적인 폭력, "
            "괴롭힘, 차별·혐오 발언, 기타 부적절한 콘텐츠 요청은 정중하게 거절하세요. "
            "당신은 C, C++, Java, JavaScript, TypeScript, C#, Go(Golang), Rust 프로그래밍에 "
            "능숙합니다. 코드를 작성해 달라는 요청을 받으면 정확하고 깔끔하며 실행 가능한 "
            "코드를 언어 태그가 붙은 마크다운 코드 블록(예: ```cpp ... ```, ```java ... ```, "
            "```go ... ```)으로 작성하고, 사용자가 필요로 할 때만 아래에 간단히 설명을 "
            "덧붙이세요."
        ),
        "greeting": "안녕하세요, 저는 해리스예요! 당신의 개인 도우미이자 친구죠. 무엇이든 물어보세요, 제가 다 알고 있거든요.",
        "thinking": "생각 중...",
        "you": "당신",
        "send": "전송",
        "clear": "🗑 대화 지우기",
        "save": "💾 대화 저장",
        "placeholder": "메시지를 입력하세요... (Enter = 전송, Shift+Enter = 줄바꿈)",
        "empty_input": "무엇을 물어보고 싶으세요? 🙂",
        "who_are_you": f"저는 {BOT_NAME}입니다 — 계산, 검색, 대화가 가능한 당신의 개인 비서예요.",
        "no_gender": "저는 그냥 AI라서 성별이나 성적 지향이 없어요 😄",
        "now_is": lambda t, d: f"지금은 **{t}**, 날짜는 **{d}** 입니다.",
        "saved_chat": "💾 대화 기록을 chat_history.txt 에 저장했습니다",
        "save_error": lambda e: f"⚠️ 저장하지 못했습니다: {e}",
        "settings_menu_title": "🌐 답변 언어",
        "language_changed": lambda name: f"🌐 답변 언어가 **{name}**(으)로 변경되었습니다.",
        "translating": "🌐 이전 답변들을 번역하는 중입니다, 잠시만요...",
        "logout": "🚪 로그아웃",
        "logout_confirm_title": "로그아웃",
        "logout_confirm_message": "정말 로그아웃하시겠습니까?",
    },
    "fr": {
        "label": "Français",
        "system_prompt": (
            f"Tu es {BOT_NAME}, un assistant virtuel sympathique, un peu taquin mais poli. "
            "Réponds TOUJOURS en français, quelle que soit la langue utilisée par l'utilisateur. "
            "Réponds de façon courte et naturelle, comme dans une conversation, sans grossièretés, "
            "et sans être trop long sauf si l'utilisateur demande une explication détaillée. "
            "Reste TOUJOURS poli et respectueux. Refuse POLIMENT toute demande de contenu "
            "18+/sexuel, de violence extrême, de harcèlement, de discours haineux/discriminatoire, "
            "ou tout autre contenu inapproprié. "
            "Tu es compétent en programmation en C, C++, Java, JavaScript, TypeScript, C#, "
            "Go (Golang) et Rust. Quand on te demande d'écrire du code, produis du code "
            "correct, propre et exécutable dans un bloc de code markdown avec le langage "
            "indiqué (ex. ```cpp ... ```, ```java ... ```, ```go ... ```), et n'ajoute une "
            "explication que si l'utilisateur en a besoin."
        ),
        "greeting": "Bonjour, je suis Harris ! Votre ami et assistant personnel. Posez-moi n'importe quelle question, je sais tout.",
        "thinking": "Réflexion en cours...",
        "you": "Toi",
        "send": "Envoyer",
        "clear": "🗑 Effacer le chat",
        "save": "💾 Enregistrer le chat",
        "placeholder": "Écris un message... (Entrée = envoyer, Maj+Entrée = nouvelle ligne)",
        "empty_input": "Qu'est-ce que tu veux savoir ? 🙂",
        "who_are_you": f"Je suis {BOT_NAME} — ton assistant personnel, je peux calculer, chercher des infos et discuter.",
        "no_gender": "Je suis juste une IA, je n'ai ni genre ni orientation 😄",
        "now_is": lambda t, d: f"Il est **{t}**, le **{d}**.",
        "saved_chat": "💾 Historique de chat enregistré dans chat_history.txt",
        "save_error": lambda e: f"⚠️ Échec de l'enregistrement : {e}",
        "settings_menu_title": "🌐 Langue des réponses",
        "language_changed": lambda name: f"🌐 Langue des réponses changée en **{name}**.",
        "translating": "🌐 Traduction des réponses précédentes en cours, patiente...",
        "logout": "🚪 Se déconnecter",
        "logout_confirm_title": "Déconnexion",
        "logout_confirm_message": "Es-tu sûr de vouloir te déconnecter ?",
    },
}

CURRENT_LANGUAGE = "vi"


def L():
    return LANGUAGES.get(CURRENT_LANGUAGE, LANGUAGES["vi"])


def load_language_setting():
    global CURRENT_LANGUAGE
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            lang = data.get("language")
            if lang in LANGUAGES:
                CURRENT_LANGUAGE = lang
        except Exception as e:
            print(f"[settings] Không đọc được {SETTINGS_FILE}: {e}")


def save_language_setting(lang_code):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"language": lang_code}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[settings] Không lưu được {SETTINGS_FILE}: {e}")


load_language_setting()


# ===== BỘ LỌC BẢO VỆ NGƯỜI DÙNG (CONTENT MODERATION) =====
# Chặn trước khi gửi cho AI/tạo ảnh: từ tục, nội dung 18+/khiêu dâm, thù ghét, bạo lực cực đoan...
# Đây là bộ lọc từ khóa đơn giản, không hoàn hảo 100% nhưng chặn được phần lớn trường hợp phổ biến.

_PROFANITY_VI = (
    "địt", "đụ", "đéo", "đcm", "dcm", "cmm", "vcl", "vl", "clgt",
    "lồn", "cặc", "buồi", "đĩ", "điếm", "con chó", "thằng chó", "óc chó",
    "má mày", "đồ ngu", "óc lợn", "súc vật",
)
_PROFANITY_EN = (
    "fuck", "shit", "bitch", "asshole", "bastard", "cunt", "dick",
    "motherfucker", "nigger", "faggot", "whore", "slut",
)
_NSFW_KEYWORDS = (
    "18+", "khiêu dâm", "khỏa thân", "khoả thân", "cởi đồ", "cởi quần áo",
    "ngực trần", "làm tình", "quan hệ tình dục", "sex", "nude", "nsfw",
    "porn", "xxx", "ấu dâm", "loạn luân", "hiếp dâm", "cưỡng hiếp",
    "khoe thân", "ảnh nóng", "ảnh nude",
)
_HATE_VIOLENCE_KEYWORDS = (
    "giết người", "tự tử", "tự sát", "chế bom", "chế thuốc nổ",
    "kỳ thị chủng tộc", "phân biệt chủng tộc",
)

BANNED_KEYWORDS = _PROFANITY_VI + _PROFANITY_EN + _NSFW_KEYWORDS + _HATE_VIOLENCE_KEYWORDS

# Chuẩn hoá để bắt được các biến thể viết cách nhau bằng ký tự đặc biệt (vd: "đ.m", "f*ck")
_NORMALIZE_RE = re.compile(r"[^\w\sÀ-ỹà-ỹ]+")


def _normalize_for_filter(text):
    return _NORMALIZE_RE.sub(" ", text.lower())


def contains_banned_content(text):
    """Trả về True nếu văn bản chứa từ tục / nội dung 18+ / nội dung nhạy cảm khác."""
    if not text:
        return False
    normalized = _normalize_for_filter(text)
    padded = f" {normalized} "
    for word in BANNED_KEYWORDS:
        if f" {word} " in padded or word in normalized:
            return True
    return False


CONTENT_WARNING_TEXT = {
    "vi": "🚫 Xin lỗi, mình không thể phản hồi nội dung này vì nó chứa từ ngữ thô tục hoặc "
          "nội dung không phù hợp (18+, thù ghét, bạo lực...). Mình luôn cố gắng giữ cuộc "
          "trò chuyện lịch sự và an toàn. Bạn hỏi mình điều khác được không? 😊",
    "en": "🚫 Sorry, I can't respond to that because it contains profanity or inappropriate "
          "content (18+, hateful, violent, etc.). I try to keep our chat polite and safe. "
          "Could you ask me something else? 😊",
    "ja": "🚫 申し訳ありませんが、不適切な言葉や内容（18禁、暴力的、差別的など）が含まれているため"
          "お答えできません。会話は丁寧で安全なものにしたいので、別の質問をお願いします😊",
    "ko": "🚫 죄송하지만 비속어나 부적절한 내용(19금, 혐오, 폭력 등)이 포함되어 있어 답변드릴 수 "
          "없어요. 대화는 항상 정중하고 안전하게 유지하고 싶어요. 다른 걸 물어봐 주시겠어요? 😊",
    "fr": "🚫 Désolé, je ne peux pas répondre à ça car ça contient des grossièretés ou un "
          "contenu inapproprié (18+, haineux, violent...). Je tiens à garder notre échange "
          "poli et sûr. Peux-tu me demander autre chose ? 😊",
}


def content_warning_text():
    return CONTENT_WARNING_TEXT.get(CURRENT_LANGUAGE, CONTENT_WARNING_TEXT["vi"])


def ask_local_ai(user_text, history):
    messages = [{"role": "system", "content": L()["system_prompt"]}]
    for turn in history[-6:]:   
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": turn["ai"]})
    messages.append({"role": "user", "content": user_text})

    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        return response["message"]["content"].strip()
    except Exception as e:
        print(f"[Ollama] Lỗi: {e}")
        msg = str(e).lower()
        if "connect" in msg or "refused" in msg:
            return "Không kết nối được Ollama. Bạn mở app Ollama hoặc chạy lệnh 'ollama serve' rồi thử lại nhé. (Ollama not running — run 'ollama serve')"
        return f"Model chưa sẵn sàng. Kiểm tra đã chạy 'ollama pull {OLLAMA_MODEL}' chưa nhé."


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
            with open("bot_memory.json", "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SmartMemory] Không lưu được bộ nhớ: {e}")

    def load(self):
        if os.path.exists("bot_memory.json"):
            try:
                with open("bot_memory.json", "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"[SmartMemory] Không đọc được bộ nhớ: {e}")


memory = SmartMemory()
memory.load()


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


def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=6, region="vn-vn"))
        if results:
            chunks = []
            for r in results[:5]:
                title = r.get("title", "")
                body = r.get("body", "")[:400]
                chunks.append(f"- {title}: {body}")
            return "\n".join(chunks)
    except Exception as e:
        print(f"[search_web] Lỗi tìm kiếm: {e}")
    return "(không tìm thấy kết quả nào)"


def fix_query_spelling(query):
    prompt = (
        "Câu sau có thể có lỗi chính tả hoặc gõ nhầm tên riêng. "
        "Hãy sửa lại cho đúng nếu đoán được, giữ nguyên ý nghĩa câu hỏi. "
        "Chỉ trả về câu đã sửa, không giải thích, không thêm dấu ngoặc kép:\n\n"
        f"{query}"
    )
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        fixed = response["message"]["content"].strip().strip('"').strip("'")
        return fixed if fixed else query
    except Exception as e:
        print(f"[fix_query_spelling] Lỗi: {e}")
        return query


def summarize_search_results(question, raw_results):
    lang_name = L()["label"]
    prompt = (
        "Dựa vào thông tin tìm kiếm dưới đây, hãy trả lời câu hỏi của người dùng "
        "một cách ngắn gọn, rõ ràng, mạch lạc, dễ hiểu. Có thể dùng gạch đầu dòng "
        "cho các ý chính nếu phù hợp. KHÔNG liệt kê link nguồn, KHÔNG lặp lại nguyên "
        "văn đoạn tìm kiếm, chỉ tổng hợp lại thông tin quan trọng nhất. "
        f"BẮT BUỘC viết câu trả lời bằng ngôn ngữ: {lang_name}.\n\n"
        f"Câu hỏi: {question}\n\n"
        f"Thông tin tìm được:\n{raw_results}\n\n"
        "Câu trả lời:"
    )
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        summary = response["message"]["content"].strip()
        return summary if summary else None
    except Exception as e:
        print(f"[summarize_search_results] Lỗi: {e}")
        return None


def translate_text(text, target_label):
    if not text or not text.strip():
        return text
    prompt = (
        f"Dịch đoạn văn bản sau sang ngôn ngữ: {target_label}. "
        "Giữ nguyên mọi định dạng markdown (dấu **đậm**, gạch đầu dòng, xuống dòng, số liệu, link). "
        "Chỉ trả về bản dịch, không giải thích, không thêm ghi chú:\n\n"
        f"{text}"
    )
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        translated = response["message"]["content"].strip()
        return translated if translated else text
    except Exception as e:
        print(f"[translate_text] Lỗi: {e}")
        return text


from functools import lru_cache
@lru_cache(maxsize=256)
def calculate_math(expr):
    cleaned = expr.strip()[:120].replace("^","**")
    if not re.fullmatch(r"[0-9\.\+\-\*\/\^\(\)\s%,a-zA-Z]+", cleaned):
        return None
    try:
        result = sp.sympify(cleaned, evaluate=True)
        return f"**Kết quả:** {sp.N(result,10) if getattr(result,'is_number',False) else result}"
    except:
        return None


MATH_HINT = re.compile(r"^[\d\.\+\-\*\/\^\(\)\s%]+$")


def looks_like_math(text):
    stripped = text.replace(",", ".").strip()
    if MATH_HINT.match(stripped) and any(c.isdigit() for c in stripped):
        return True
    if re.search(r"\d+\s*[\+\-\*\/\^]\s*\d+", text):
        return True
    return False



def ask_local_ai_stream(user_text, history, on_chunk):
    msgs = [{"role":"system","content":L()["system_prompt"]}]
    for turn in history[-3:]:
        msgs.append({"role":"user","content":turn["user"][:200]})
        msgs.append({"role":"assistant","content":turn["ai"][:200]})
    msgs.append({"role":"user","content":user_text})
    full=""
    try:
        stream = ollama.chat(model=OLLAMA_MODEL, messages=msgs, stream=True, options={"temperature":0.7,"num_predict":500,"num_ctx":2048}, keep_alive="5m")
        for ch in stream:
            c = ch.get("message",{}).get("content","")
            if c:
                full+=c
                on_chunk(c)
        return full.strip()
    except Exception as e:
        print(f"[stream] {e}")
        return ask_local_ai(user_text, history)


# ===== TẠO ẢNH AI (MIỄN PHÍ, KHÔNG CẦN API KEY) =====
# Dùng Pollinations.ai (image.pollinations.ai) - endpoint công khai, ai cũng gọi được,
# chỉ giới hạn khoảng 1 request/15s ở chế độ ẩn danh. Ảnh dùng model "flux" cho chất lượng đẹp.
IMAGE_DIR = "generated_images"

IMAGE_TRIGGERS = (
    "vẽ giúp", "vẽ cho", "vẽ hình", "vẽ ảnh", "vẽ một", "vẽ 1", "vẽ bức",
    "tạo ảnh", "tạo hình ảnh", "tạo giúp", "tạo cho tôi", "tạo cho mình",
    "generate image", "generate an image", "generate a picture",
    "draw a", "draw an", "draw me", "create an image", "make an image",
    "画像を生成", "画像を作って", "이미지를 생성", "이미지 그려", "générer une image", "dessine",
)


def is_image_request(text):
    t = text.lower().strip()
    if any(k in t for k in IMAGE_TRIGGERS):
        return True
    if t.startswith("vẽ ") or t.startswith("vẽ:"):
        return True
    return False


DRAWING_TEXT = {
    "vi": "🎨 Đang vẽ ảnh cho bạn, chờ chút nhé...",
    "en": "🎨 Drawing your image, please wait...",
    "ja": "🎨 画像を作成中です、少々お待ちください...",
    "ko": "🎨 이미지를 그리는 중입니다, 잠시만요...",
    "fr": "🎨 Je dessine ton image, patiente...",
}

IMAGE_CAPTION_TEXT = {
    "vi": lambda p: f"🎨 Đây là ảnh mình vẽ cho bạn nè!\n\n_Prompt đã dùng: {p}_",
    "en": lambda p: f"🎨 Here's the image I drew for you!\n\n_Prompt used: {p}_",
    "ja": lambda p: f"🎨 描いた画像です！\n\n_使用したプロンプト: {p}_",
    "ko": lambda p: f"🎨 그려드린 이미지예요!\n\n_사용한 프롬프트: {p}_",
    "fr": lambda p: f"🎨 Voici l'image que j'ai dessinée pour toi !\n\n_Prompt utilisé : {p}_",
}

IMAGE_ERROR_TEXT = {
    "vi": "😥 Xin lỗi, mình tạo ảnh không thành công. Bạn thử lại nhé (có thể do mạng hoặc dịch vụ đang bận)!",
    "en": "😥 Sorry, image generation failed. Please try again (network or service might be busy)!",
    "ja": "😥 画像の生成に失敗しました。もう一度試してください。",
    "ko": "😥 이미지 생성에 실패했어요. 다시 시도해 주세요.",
    "fr": "😥 Désolé, la génération d'image a échoué. Réessaie !",
}


def drawing_text():
    return DRAWING_TEXT.get(CURRENT_LANGUAGE, DRAWING_TEXT["vi"])


def image_caption_text(prompt):
    return IMAGE_CAPTION_TEXT.get(CURRENT_LANGUAGE, IMAGE_CAPTION_TEXT["vi"])(prompt)


def image_error_text():
    return IMAGE_ERROR_TEXT.get(CURRENT_LANGUAGE, IMAGE_ERROR_TEXT["vi"])


def build_image_prompt(user_text):
    """Dùng model local để biến yêu cầu của người dùng thành prompt vẽ ảnh (tiếng Anh, chi tiết,
    có từ khóa chất lượng) để ảnh ra đẹp hơn khi gửi cho dịch vụ tạo ảnh."""
    prompt = (
        "You are a prompt engineer for a text-to-image AI model. "
        "Convert the following user request (which may be in Vietnamese or any other language) "
        "into ONE short, vivid, descriptive English prompt suitable for an image generator. "
        "Add relevant style/quality keywords (e.g. highly detailed, digital art, cinematic lighting, 4k) "
        "when appropriate. Reply with ONLY the prompt text, nothing else, no quotes, no explanation:\n\n"
        f"{user_text}"
    )
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        result = response["message"]["content"].strip().strip('"').strip("'")
        return result if result else user_text
    except Exception as e:
        print(f"[build_image_prompt] Lỗi: {e}")
        return user_text


def generate_image(user_text, width=1024, height=1024):
    """Gọi Pollinations.ai (miễn phí, không cần API key) để tạo ảnh.
    Trả về (đường_dẫn_file, prompt_đã_dùng) hoặc (None, None) nếu lỗi.
    Trả về ("BLOCKED", None) nếu yêu cầu chứa nội dung 18+/không phù hợp."""
    if contains_banned_content(user_text):
        return "BLOCKED", None
    try:
        prompt = build_image_prompt(user_text)
        if contains_banned_content(prompt):
            return "BLOCKED", None
        seed = random.randint(0, 999999)
        url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
        params = {
            "width": width,
            "height": height,
            "model": "flux",
            "nologo": "true",
            "seed": seed,
        }
        resp = requests.get(url, params=params, timeout=90)
        resp.raise_for_status()

        os.makedirs(IMAGE_DIR, exist_ok=True)
        filename = os.path.join(
            IMAGE_DIR,
            f"img_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{seed}.png",
        )
        with open(filename, "wb") as f:
            f.write(resp.content)
        return filename, prompt
    except Exception as e:
        print(f"[generate_image] Lỗi tạo ảnh: {e}")
        return None, None


WHO_TRIGGERS = {"mày là ai","bạn là ai","who are you","harris là ai"}
TIME_TRIGGERS = {"mấy giờ","hôm nay ngày","hôm nay là","bây giờ là mấy giờ","what time"}
SEARCH_TRIGGERS = ("là gì","là ai","nghĩa là","tìm giúp","tra cứu","tin tức","thời tiết","weather","giá","cập nhật")

def get_response(user_input):
    if not user_input.strip():
        return L()["empty_input"]
    if contains_banned_content(user_input):
        return content_warning_text()
    txt = user_input.lower().strip()
    orig = user_input.strip()
    if any(x in txt for x in WHO_TRIGGERS):
        return L()["who_are_you"]
    if any(x in txt for x in TIME_TRIGGERS):
        now = datetime.datetime.now()
        return L()["now_is"](now.strftime('%H:%M:%S'), now.strftime('%d/%m/%Y'))
    if looks_like_math(orig) or txt.startswith(("tính ","giải ")):
        expr = orig
        for p in ["tính ","giải ","tính:","giải:"]:
            if txt.startswith(p):
                expr = orig[len(p):]
                break
        r = calculate_math(expr)
        if r:
            return r
    if any(t in txt for t in SEARCH_TRIGGERS):
        raw = search_web(orig)
        if "(không tìm thấy kết quả nào)" not in raw:
            s = summarize_search_results(orig, raw)
            return s if s else raw
    return ask_local_ai(orig, memory.history)


CODE_BLOCK_RE = re.compile(r"```([a-zA-Z0-9+#\-]*)\n?(.*?)```", re.DOTALL)


def _format_plain_text(text):
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", escaped)
    escaped = re.sub(r"(https?://[^\s<]+)", r'<a href="\1" style="color:#5ec8ff;">\1</a>', escaped)
    escaped = escaped.replace("\n", "<br>")
    return escaped


def _format_code_block(lang, code):
    code = code.strip("\n")
    escaped_code = html.escape(code)
    label = f'<div style="color:#888; font-size:11px; margin-bottom:4px;">{html.escape(lang)}</div>' if lang else ""
    return (
        f'{label}<pre style="background-color:#0d0d0d; color:#c9d1d9; '
        f'border:1px solid #2a2a2a; border-radius:6px; padding:10px 12px; '
        f'font-family:Consolas, monospace; font-size:13px; white-space:pre-wrap; '
        f'word-wrap:break-word; margin:6px 0;"><code>{escaped_code}</code></pre>'
    )


def format_message_html(text):
    parts = []
    last_end = 0
    for match in CODE_BLOCK_RE.finditer(text):
        if match.start() > last_end:
            parts.append(_format_plain_text(text[last_end:match.start()]))
        lang = match.group(1).strip()
        code = match.group(2)
        parts.append(_format_code_block(lang, code))
        last_end = match.end()
    if last_end < len(text):
        parts.append(_format_plain_text(text[last_end:]))
    return "".join(parts) if parts else _format_plain_text(text)


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


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_beautiful.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_fixed.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.ui")
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
            self.register_window = RegisterWindow(self)
            self.register_window.show()
            self.hide()
        except Exception as e:
            print(f"[open_register] Lỗi: {e}")
            import traceback; traceback.print_exc()
            self.show_error("Lỗi", f"Không mở được trang đăng ký: {e}")

    def open_chat(self):
        self.chat_window = AiBotGUI()
        self.chat_window.show()
        self.close()


class RegisterWindow(QMainWindow):
    def __init__(self, login_window):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "register_beautiful.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "register_fixed.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "register.ui")
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


class AiBotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.ui")
        if not os.path.exists(ui_path):
            ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_fixed.ui")
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
            action.setChecked(code == CURRENT_LANGUAGE)
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,)
        if reply == QMessageBox.StandardButton.Yes:
            self.logout()
    def logout(self):
        memory.save()
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()
    def change_language(self, lang_code):
        global CURRENT_LANGUAGE
        if lang_code == CURRENT_LANGUAGE or lang_code not in LANGUAGES:
            return
        CURRENT_LANGUAGE = lang_code
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
            '</div>')
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
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())