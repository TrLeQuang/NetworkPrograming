import os
import sys
import threading
import importlib.util

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

# Load protocol.py bằng path tuyệt đối (VS2022-safe)
PROTOCOL_PATH = os.path.join(THIS_DIR, "protocol.py")
if not os.path.exists(PROTOCOL_PATH):
    raise FileNotFoundError(f"Không tìm thấy protocol.py tại: {PROTOCOL_PATH}")

spec = importlib.util.spec_from_file_location("server_protocol", PROTOCOL_PATH)
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)

# map function
decode_message = protocol.decode_message
encode_message = protocol.encode_message
build_error = protocol.build_error
build_private = protocol.build_private
build_group = protocol.build_group




class ClientHandler(threading.Thread):
    def __init__(self, client_socket, address, server, user_manager):
        super().__init__(daemon=True)
        self.client_socket = client_socket
        self.address = address
        self.server = server
        self.user_manager = user_manager
        self.username = None
        self.running = True

    def run(self):
        buffer = b""
        try:
            while self.running:
                chunk = self.client_socket.recv(4096)
                if not chunk:
                    break
                buffer += chunk

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line:
                        self._handle_one(line)
        except Exception as e:
            self.server.log(f"Lỗi recv từ {self.username or self.address}: {e}", "ERROR")
        finally:
            self.close()

    def _handle_one(self, raw: bytes):
        data = decode_message(raw)
        if data is None:
            return

        t = data.get("type")

        if t == "login":
            self._login(data)
        elif t == "logout":
            self.running = False

        elif t == "private":
            self._private(data)

        elif t == "create_room":
            self._create_room(data)

        elif t == "join_room":
            self._join_room(data)

        elif t == "leave_room":
            self._leave_room(data)

        elif t == "group":
            self._group(data)

        else:
            pass

    # ===== Login =====
    def _login(self, data: dict):
        username = (data.get("user") or "").strip()
        if not username:
            self.send_raw(build_error("Username không hợp lệ"))
            return

        if self.user_manager.has_user(username):
            self.send_raw(build_error("Username đã tồn tại"))
            return

        self.username = username
        self.user_manager.add_user(username, self)

        self.server.log(f"✅ {username} login ({self.address[0]}:{self.address[1]})", "SUCCESS")
        self.server.broadcast_system(f"{username} đã tham gia")

        self.server.send_user_list_all()
        self.server.send_room_list_all()
        self.server.update_counts()

    # ===== Private 1-1 =====
    def _private(self, data: dict):
        if not self.username:
            self.send_raw(build_error("Bạn chưa login"))
            return

        to_user = (data.get("to") or "").strip()
        msg = (data.get("msg") or "").strip()
        if not to_user:
            self.send_raw(build_error("Thiếu người nhận"))
            return
        if not msg:
            return
        if to_user == self.username:
            self.send_raw(build_error("Không thể nhắn cho chính mình"))
            return

        target = self.user_manager.get_handler(to_user)
        if not target:
            self.send_raw(build_error(f"User '{to_user}' không online"))
            return

        payload = build_private(self.username, to_user, msg)

        # gửi cho người nhận + echo cho người gửi
        target.send_raw(payload)
        self.send_raw(payload)

        self.server.log(f"💬 PRIVATE {self.username} -> {to_user}: {msg}", "CLIENT")

    # ===== Rooms =====
    def _create_room(self, data: dict):
        if not self.username:
            self.send_raw(build_error("Bạn chưa login"))
            return

        room = (data.get("room") or "").strip()
        if not room:
            self.send_raw(build_error("Tên phòng không hợp lệ"))
            return

        ok = self.server.room_manager.create_room(room)
        if not ok:
            self.send_raw(build_error("Phòng đã tồn tại"))
            return

        # creator auto-join cho tiện dùng
        self.server.room_manager.join(room, self.username)

        self.server.log(f"🧩 {self.username} tạo phòng '{room}'", "SUCCESS")
        self.server.broadcast_system(f"{self.username} đã tạo phòng '{room}'")
        self.server.send_room_list_all()

    def _join_room(self, data: dict):
        if not self.username:
            self.send_raw(build_error("Bạn chưa login"))
            return

        room = (data.get("room") or "").strip()
        if not self.server.room_manager.room_exists(room):
            self.send_raw(build_error("Phòng không tồn tại"))
            return

        self.server.room_manager.join(room, self.username)
        self.server.log(f"➕ {self.username} join '{room}'", "INFO")
        self.server.broadcast_system(f"{self.username} đã join phòng '{room}'")
        self.server.send_room_list_all()

    def _leave_room(self, data: dict):
        if not self.username:
            self.send_raw(build_error("Bạn chưa login"))
            return

        room = (data.get("room") or "").strip()
        if not self.server.room_manager.room_exists(room):
            self.send_raw(build_error("Phòng không tồn tại"))
            return

        self.server.room_manager.leave(room, self.username)
        self.server.log(f"➖ {self.username} leave '{room}'", "INFO")
        self.server.broadcast_system(f"{self.username} đã rời phòng '{room}'")
        self.server.send_room_list_all()

    def _group(self, data: dict):
        if not self.username:
            self.send_raw(build_error("Bạn chưa login"))
            return

        room = (data.get("room") or "").strip()
        msg = (data.get("msg") or "").strip()
        if not room:
            self.send_raw(build_error("Thiếu tên phòng"))
            return
        if not msg:
            return

        members = self.server.room_manager.members(room)
        if self.username not in members:
            self.send_raw(build_error("Bạn chưa join phòng này"))
            return

        payload = build_group(room, self.username, msg)
        self.server.broadcast_room(room, payload)

        self.server.log(f"💬 ROOM({room}) {self.username}: {msg}", "CLIENT")

    # ===== Send helpers =====
    def send_raw(self, data: dict):
        try:
            self.client_socket.sendall(encode_message(data) + b"\n")
        except Exception:
            self.running = False

    def close(self):
        self.running = False

        if self.username:
            # remove user online + remove from rooms
            try:
                self.server.room_manager.remove_user_everywhere(self.username)
            except Exception:
                pass

            try:
                self.user_manager.remove_user(self.username)
            except Exception:
                pass

            self.server.broadcast_system(f"{self.username} đã rời khỏi")
            self.server.send_user_list_all()
            self.server.send_room_list_all()
            self.server.update_counts()

        self.server.remove_client(self)

        try:
            self.client_socket.close()
        except Exception:
            pass
