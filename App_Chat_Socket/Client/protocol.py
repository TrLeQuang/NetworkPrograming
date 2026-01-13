import json
from datetime import datetime

ENCODING = "utf-8"


def encode_message(data: dict) -> bytes:
    """
    Chuyển dict Python thành bytes JSON để gửi qua socket.
    Dùng chung cho cả server và client.
    """
    # ensure_ascii=False để giữ tiếng Việt không bị \\uXXXX
    text = json.dumps(data, ensure_ascii=False)
    return text.encode(ENCODING)


def decode_message(raw: bytes) -> dict | None:
    """
    Chuyển bytes nhận được thành dict JSON.
    Trả về None nếu lỗi (không phải JSON hợp lệ).
    """
    try:
        text = raw.decode(ENCODING)
        return json.loads(text)
    except Exception:
        return None


def current_timestamp() -> str:
    """Trả về timestamp dạng chuỗi, ví dụ '2026-01-13 14:30:00'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ========== Các hàm build message ==========

def build_login(user: str) -> dict:
    """
    Gói login client gửi lên server.
    Ví dụ: { "type": "login", "user": "A" }
    """
    return {
        "type": "login",
        "user": user
    }


def build_logout(user: str) -> dict:
    """
    Gói logout client gửi lên server.
    Ví dụ: { "type": "logout", "user": "A" }
    """
    return {
        "type": "logout",
        "user": user
    }


def build_chat_message(sender: str, msg: str) -> dict:
    """
    Gói chat server broadcast tới mọi client.
    Ví dụ:
    {
      "type": "message",
      "from": "A",
      "msg": "hi",
      "timestamp": "2026-01-13 14:30:00"
    }
    """
    return {
        "type": "message",
        "from": sender,
        "msg": msg,
        "timestamp": current_timestamp()
    }


def build_system_message(msg: str) -> dict:
    """
    Gói system message (join/leave, thông báo).
    Ví dụ:
    {
      "type": "system",
      "msg": "A đã tham gia phòng chat",
      "timestamp": "2026-01-13 14:30:00"
    }
    """
    return {
        "type": "system",
        "msg": msg,
        "timestamp": current_timestamp()
    }


def build_user_list(users: list[str]) -> dict:
    """
    Gói danh sách user online server gửi cho client.
    Ví dụ: { "type": "user_list", "users": ["A", "B"] }
    """
    return {
        "type": "user_list",
        "users": users
    }


def build_error(msg: str) -> dict:
    """
    Gói báo lỗi từ server gửi cho client.
    Ví dụ: { "type": "error", "msg": "Username đã tồn tại" }
    """
    return {
        "type": "error",
        "msg": msg
    }
