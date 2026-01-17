import threading
import os
import importlib.util

# ===== Load protocol.py bằng đường dẫn tuyệt đối (ổn định trong VS2022) =====
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROTOCOL_PATH = os.path.join(_THIS_DIR, "protocol.py")

_spec = importlib.util.spec_from_file_location("server_protocol", _PROTOCOL_PATH)
_protocol = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_protocol)

encode_message = _protocol.encode_message
decode_message = _protocol.decode_message
build_chat_message = _protocol.build_chat_message
build_system_message = _protocol.build_system_message
build_user_list = _protocol.build_user_list
build_error = _protocol.build_error


class ClientHandler(threading.Thread):
    """
    Xử lý kết nối của từng client.
    Thread riêng cho mỗi client.
    Tương thích với Protocol JSON.
    """

    def __init__(self, client_socket, address, server, user_manager):
        super().__init__()
        self.client_socket = client_socket
        self.address = address
        self.server = server
        self.user_manager = user_manager

        self.username = None
        self.running = True

    def run(self):
        """Thread chính xử lý client"""
        try:
            buffer = b""

            while self.running:
                try:
                    chunk = self.client_socket.recv(4096)
                    if not chunk:
                        break

                    buffer += chunk

                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        if line:
                            self._process_message(line)

                except Exception as e:
                    self.server.log(
                        f"Lỗi khi nhận message từ {self.username or self.address}: {e}",
                        "ERROR",
                    )
                    break

        except Exception as e:
            self.server.log(f"Lỗi với client {self.address}: {e}", "ERROR")

        finally:
            self.close()

    def _process_message(self, raw: bytes):
        data = decode_message(raw)

        if data is None:
            self.server.log(
                f"Message không hợp lệ từ {self.username or self.address}", "WARNING"
            )
            return

        msg_type = data.get("type")

        if msg_type == "login":
            self._handle_login(data)
        elif msg_type == "logout":
            self._handle_logout(data)
        elif msg_type == "message":
            self._handle_chat_message(data)
        else:
            self.server.log(f"Message type không xác định: {msg_type}", "WARNING")

    def _handle_login(self, data: dict):
        username = data.get("user", "").strip()

        if not username:
            self.send_raw(build_error("Username không hợp lệ"))
            return

        # Kiểm tra trùng username
        if self.user_manager.has_user(username):
            self.send_raw(build_error("Username đã tồn tại, vui lòng chọn tên khác"))
            self.server.log(f"❌ Login thất bại: '{username}' đã tồn tại", "WARNING")
            return

        # Add user online
        self.username = username
        self.user_manager.add_user(username, self)

        self.server.log(
            f"✅ User '{username}' đã login từ {self.address[0]}:{self.address[1]}",
            "SUCCESS",
        )

        # Broadcast join + user_list
        self.server.broadcast(build_system_message(f"{username} đã tham gia phòng chat"))
        self._broadcast_user_list()

        # Refresh count ngay sau login
        self.server.refresh_online_count()

    def _handle_logout(self, data: dict):
        username = data.get("user", "")
        self.server.log(f"👋 User '{username}' đã logout", "INFO")
        self.running = False

    def _handle_chat_message(self, data: dict):
        username = data.get("user", "Unknown")
        msg = data.get("msg", "")

        if not msg.strip():
            return

        self.server.log(f"💬 {username}: {msg}", "CLIENT")
        self.server.broadcast(build_chat_message(username, msg))

    def send_raw(self, data: dict):
        """Gửi dict data (JSON bytes) kèm delimiter \\n"""
        try:
            raw_bytes = encode_message(data)
            self.client_socket.sendall(raw_bytes + b"\n")
        except Exception as e:
            self.server.log(f"Không thể gửi message đến {self.username}: {e}", "ERROR")
            self.running = False

    def _broadcast_user_list(self):
        online_users = self.user_manager.get_online_users()
        self.server.broadcast(build_user_list(online_users))

    def close(self):
        """Đóng kết nối và cleanup"""
        self.running = False

        # Nếu user đã login thì remove + broadcast leave
        if self.username:
            try:
                self.user_manager.remove_user(self.username)
            except:
                pass

            leave_msg = build_system_message(f"{self.username} đã rời khỏi phòng chat")
            self.server.log(f"👋 User '{self.username}' đã rời khỏi", "WARNING")
            self.server.broadcast(leave_msg)

            # Update user list
            self._broadcast_user_list()

        # Remove khỏi list connections
        self.server.remove_client(self)

        # Refresh count sau khi close
        self.server.refresh_online_count()

        try:
            self.client_socket.close()
        except:
            pass
