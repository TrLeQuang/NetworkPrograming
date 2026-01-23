import json
import base64
import os
import mimetypes
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

# ===== File handling =====
def encode_file(file_path: str) -> dict | None:
    """
    Đọc file và encode thành base64
    Return: {"name": "filename.ext", "data": "base64...", "type": "image/png", "size": 12345}
    """
    try:
        if not os.path.exists(file_path):
            return None
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Giới hạn 5MB
        if file_size > 5 * 1024 * 1024:
            return None
        
        # Đọc file
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Encode base64
        b64_data = base64.b64encode(file_data).decode('ascii')
        
        # Xác định MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        return {
            "name": file_name,
            "data": b64_data,
            "type": mime_type,
            "size": file_size
        }
    except Exception as e:
        print(f"Error encoding file: {e}")
        return None

def decode_file(file_dict: dict, save_dir: str = "downloads") -> str | None:
    """
    Decode base64 và lưu file (chỉ khi được gọi)
    Return: đường dẫn file đã lưu, hoặc None nếu lỗi
    """
    try:
        file_name = file_dict.get("name", "unknown")
        b64_data = file_dict.get("data", "")
        
        if not b64_data:
            return None
        
        # Tạo thư mục downloads nếu chưa có
        os.makedirs(save_dir, exist_ok=True)
        
        # Decode base64
        file_data = base64.b64decode(b64_data)
        
        # Tạo tên file unique nếu đã tồn tại
        save_path = os.path.join(save_dir, file_name)
        counter = 1
        base_name, ext = os.path.splitext(file_name)
        while os.path.exists(save_path):
            save_path = os.path.join(save_dir, f"{base_name}_{counter}{ext}")
            counter += 1
        
        # Lưu file
        with open(save_path, "wb") as f:
            f.write(file_data)
        
        return save_path
    except Exception as e:
        print(f"Error decoding file: {e}")
        return None

def get_file_preview_data(file_dict: dict) -> bytes | None:
    """
    Chỉ decode base64 để preview, KHÔNG lưu file
    Return: bytes data để hiển thị, hoặc None nếu lỗi
    """
    try:
        b64_data = file_dict.get("data", "")
        if not b64_data:
            return None
        return base64.b64decode(b64_data)
    except Exception as e:
        print(f"Error getting preview data: {e}")
        return None

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
def build_private(sender: str, to_user: str, msg: str, file_data: dict = None) -> dict:
    data = {
        "type": "private",
        "from": sender,
        "to": to_user,
        "msg": msg,
        "timestamp": now_ts(),
    }
    if file_data:
        data["file"] = file_data
    return data

# ===== Rooms =====
def build_room_list(rooms_snapshot: list[dict]) -> dict:
    return {"type": "room_list", "rooms": rooms_snapshot}

def build_create_room(user: str, room: str) -> dict:
    return {"type": "create_room", "user": user, "room": room}

def build_join_room(user: str, room: str) -> dict:
    return {"type": "join_room", "user": user, "room": room}

def build_leave_room(user: str, room: str) -> dict:
    return {"type": "leave_room", "user": user, "room": room}

def build_group(room: str, sender: str, msg: str, file_data: dict = None) -> dict:
    data = {
        "type": "group",
        "room": room,
        "from": sender,
        "msg": msg,
        "timestamp": now_ts(),
    }
    if file_data:
        data["file"] = file_data
    return data