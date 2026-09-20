"""Cấu hình chung + đa ngôn ngữ."""
import json
import os

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
