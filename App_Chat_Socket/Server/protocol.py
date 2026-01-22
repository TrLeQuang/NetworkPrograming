import json
from datetime import datetime

ENCODING = "utf-8"


def encode_message(data: dict) -> bytes:
    text = json.dumps(data, ensure_ascii=False)
    return text.encode(ENCODING)


def decode_message(raw: bytes) -> dict | None:
    try:
        text = raw.decode(ENCODING)
        return json.loads(text)
    except Exception:
        return None


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ===== Basic =====
def build_login(user: str) -> dict:
    return {"type": "login", "user": user}


def build_logout(user: str) -> dict:
    return {"type": "logout", "user": user}


def build_user_list(users: list[str]) -> dict:
    return {"type": "user_list", "users": users}


def build_system(msg: str, room: str | None = None) -> dict:
    data = {
        "type": "system",
        "msg": msg,
        "timestamp": now_ts()
    }
    if room:
        data["room"] = room
    return data



def build_error(msg: str) -> dict:
    return {"type": "error", "msg": msg}


# ===== Private 1-1 =====
def build_private(sender: str, to_user: str, msg: str) -> dict:
    return {
        "type": "private",
        "from": sender,
        "to": to_user,
        "msg": msg,
        "timestamp": now_ts(),
    }


# ===== Rooms =====
def build_room_list(rooms_snapshot: list[dict]) -> dict:
    # rooms_snapshot: [{"name":"room1","members":["A","B"]}, ...]
    return {"type": "room_list", "rooms": rooms_snapshot}


def build_create_room(user: str, room: str) -> dict:
    return {"type": "create_room", "user": user, "room": room}


def build_join_room(user: str, room: str) -> dict:
    return {"type": "join_room", "user": user, "room": room}


def build_leave_room(user: str, room: str) -> dict:
    return {"type": "leave_room", "user": user, "room": room}


def build_group(room: str, sender: str, msg: str) -> dict:
    return {
        "type": "group",
        "room": room,
        "from": sender,
        "msg": msg,
        "timestamp": now_ts(),
    }
