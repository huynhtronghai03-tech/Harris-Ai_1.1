"""Bộ lọc nội dung nhạy cảm."""
import re
import config

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
    return CONTENT_WARNING_TEXT.get(config.CURRENT_LANGUAGE, CONTENT_WARNING_TEXT["vi"])

