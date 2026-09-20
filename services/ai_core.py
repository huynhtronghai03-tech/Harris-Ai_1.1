"""AI core: Ollama, search, math, translate, image, get_response, format HTML."""
import re
import html
import datetime
import random
import os
import requests
from urllib.parse import quote
from ddgs import DDGS
import sympy as sp
import ollama
from functools import lru_cache

from config import BOT_NAME, OLLAMA_MODEL, L
import config
from moderation import contains_banned_content, content_warning_text
from memory import memory

IMAGE_TRIGGERS = (
    "tạo ảnh",
    "tạo hình ảnh",
    "generate image",
    "create image",
    "draw image",
    "vẽ ảnh",
    "vẽ hình",
    "vẽ cho tôi",
    "tạo cho tôi một bức ảnh",
    "generate a picture",
    "create a picture",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(BASE_DIR, "generated_images")


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
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
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
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
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
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        translated = response["message"]["content"].strip()
        return translated if translated else text
    except Exception as e:
        print(f"[translate_text] Lỗi: {e}")
        return text


@lru_cache(maxsize=256)
def calculate_math(expr):
    cleaned = expr.strip()[:120].replace("^", "**")

    if not re.fullmatch(
        r"[0-9\.\+\-\*\/\^\(\)\s%,a-zA-Z]+",
        cleaned
    ):
        return None

    try:
        result = sp.sympify(cleaned, evaluate=True)

        return (
            f"**Kết quả:** "
            f"{sp.N(result, 10) if getattr(result, 'is_number', False) else result}"
        )
    except Exception:
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
    msgs = [
        {
            "role": "system",
            "content": L()["system_prompt"]
        }
    ]

    for turn in history[-3:]:
        msgs.append({
            "role": "user",
            "content": turn["user"][:200]
        })
        msgs.append({
            "role": "assistant",
            "content": turn["ai"][:200]
        })

    msgs.append({
        "role": "user",
        "content": user_text
    })

    full = ""

    try:
        stream = ollama.chat(
            model=OLLAMA_MODEL,
            messages=msgs,
            stream=True,
            options={
                "temperature": 0.7,
                "num_predict": 500,
                "num_ctx": 2048
            },
            keep_alive="5m"
        )

        for ch in stream:
            c = ch.get("message", {}).get("content", "")

            if c:
                full += c
                on_chunk(c)

        return full.strip()

    except Exception as e:
        print(f"[stream] {e}")
        return ask_local_ai(user_text, history)


# ===== TẠO ẢNH AI =====

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
    return DRAWING_TEXT.get(
        config.CURRENT_LANGUAGE,
        DRAWING_TEXT["vi"]
    )


def image_caption_text(prompt):
    return IMAGE_CAPTION_TEXT.get(
        config.CURRENT_LANGUAGE,
        IMAGE_CAPTION_TEXT["vi"]
    )(prompt)


def image_error_text():
    return IMAGE_ERROR_TEXT.get(
        config.CURRENT_LANGUAGE,
        IMAGE_ERROR_TEXT["vi"]
    )


def build_image_prompt(user_text):
    """Dùng model local để biến yêu cầu của người dùng thành prompt vẽ ảnh."""

    prompt = (
        "You are a prompt engineer for a text-to-image AI model. "
        "Convert the following user request (which may be in Vietnamese or any other language) "
        "into ONE short, vivid, descriptive English prompt suitable for an image generator. "
        "Add relevant style/quality keywords (e.g. highly detailed, digital art, cinematic lighting, 4k) "
        "when appropriate. Reply with ONLY the prompt text, nothing else, no quotes, no explanation:\n\n"
        f"{user_text}"
    )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )

        result = response["message"]["content"].strip().strip('"').strip("'")

        return result if result else user_text

    except Exception as e:
        print(f"[build_image_prompt] Lỗi: {e}")
        return user_text


def generate_image(user_text, width=1024, height=1024):
    """Gọi Pollinations.ai để tạo ảnh."""

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

        resp = requests.get(
            url,
            params=params,
            timeout=90
        )

        resp.raise_for_status()

        os.makedirs(
            IMAGE_DIR,
            exist_ok=True
        )

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


WHO_TRIGGERS = {
    "mày là ai",
    "bạn là ai",
    "who are you",
    "harris là ai"
}


TIME_TRIGGERS = {
    "mấy giờ",
    "hôm nay ngày",
    "hôm nay là",
    "bây giờ là mấy giờ",
    "what time"
}


SEARCH_TRIGGERS = (
    "là gì",
    "là ai",
    "nghĩa là",
    "tìm giúp",
    "tra cứu",
    "tin tức",
    "thời tiết",
    "weather",
    "giá",
    "cập nhật"
)


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

        return L()["now_is"](
            now.strftime("%H:%M:%S"),
            now.strftime("%d/%m/%Y")
        )

    if looks_like_math(orig) or txt.startswith(("tính ", "giải ")):
        expr = orig

        for p in [
            "tính ",
            "giải ",
            "tính:",
            "giải:"
        ]:
            if txt.startswith(p):
                expr = orig[len(p):]
                break

        r = calculate_math(expr)

        if r:
            return r

    if any(t in txt for t in SEARCH_TRIGGERS):
        raw = search_web(orig)

        if "(không tìm thấy kết quả nào)" not in raw:
            s = summarize_search_results(
                orig,
                raw
            )

            return s if s else raw

    return ask_local_ai(
        orig,
        memory.history
    )


CODE_BLOCK_RE = re.compile(
    r"```([a-zA-Z0-9+#\-]*)\n?(.*?)```",
    re.DOTALL
)


def _format_plain_text(text):
    escaped = html.escape(text)

    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        escaped
    )

    escaped = re.sub(
        r"(?<!\w)_(.+?)_(?!\w)",
        r"<i>\1</i>",
        escaped
    )

    escaped = re.sub(
        r"(https?://[^\s<]+)",
        r'<a href="\1" style="color:#5ec8ff;">\1</a>',
        escaped
    )

    escaped = escaped.replace(
        "\n",
        "<br>"
    )

    return escaped


def _format_code_block(lang, code):
    code = code.strip("\n")

    escaped_code = html.escape(code)

    label = (
        f'<div style="color:#888; font-size:11px; margin-bottom:4px;">'
        f'{html.escape(lang)}</div>'
        if lang
        else ""
    )

    return (
        f'{label}'
        f'<pre style="background-color:#0d0d0d; color:#c9d1d9; '
        f'border:1px solid #2a2a2a; border-radius:6px; padding:10px 12px; '
        f'font-family:Consolas, monospace; font-size:13px; white-space:pre-wrap; '
        f'word-wrap:break-word; margin:6px 0;">'
        f'<code>{escaped_code}</code>'
        f'</pre>'
    )


def format_message_html(text):
    parts = []
    last_end = 0

    for match in CODE_BLOCK_RE.finditer(text):
        if match.start() > last_end:
            parts.append(
                _format_plain_text(
                    text[last_end:match.start()]
                )
            )

        lang = match.group(1).strip()
        code = match.group(2)

        parts.append(
            _format_code_block(
                lang,
                code
            )
        )

        last_end = match.end()

    if last_end < len(text):
        parts.append(
            _format_plain_text(
                text[last_end:]
            )
        )

    return (
        "".join(parts)
        if parts
        else _format_plain_text(text)
    )