import socket
import threading
from typing import Callable, Optional
from protocol import (
    encode_message, decode_message, encode_file,
    build_login, build_logout,
    build_create_room, build_join_room, build_leave_room,
    build_private, build_group
)

class ClientNetwork:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        self.on_message: Optional[Callable[[dict], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None

    def set_on_message(self, cb: Callable[[dict], None]):
        self.on_message = cb

    def set_on_disconnect(self, cb: Callable[[], None]):
        self.on_disconnect = cb

    def connect(self) -> bool:
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.running = True
            threading.Thread(target=self._recv_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False

    def disconnect(self):
        self.running = False
        self.connected = False
        try:
            if self.socket:
                self.socket.close()
        except Exception:
            pass
        self.socket = None

    def send_raw(self, data: dict) -> bool:
        if not self.connected or not self.socket:
            return False
        try:
            self.socket.sendall(encode_message(data) + b"\n")
            return True
        except Exception as e:
            print(f"Send error: {e}")
            self._handle_disconnect()
            return False

    # ===== API =====
    def send_login(self, user: str) -> bool:
        return self.send_raw(build_login(user))

    def send_logout(self, user: str) -> bool:
        return self.send_raw(build_logout(user))

    def send_private(self, from_user: str, to_user: str, msg: str, file_path: str = None) -> bool:
        """Gửi tin nhắn riêng, có thể kèm file"""
        file_data = None
        if file_path:
            file_data = encode_file(file_path)
            if not file_data:
                print(f"Failed to encode file: {file_path}")
                return False
        
        return self.send_raw(build_private(from_user, to_user, msg, file_data))

    def create_room(self, user: str, room: str) -> bool:
        return self.send_raw(build_create_room(user, room))

    def join_room(self, user: str, room: str) -> bool:
        return self.send_raw(build_join_room(user, room))

    def leave_room(self, user: str, room: str) -> bool:
        return self.send_raw(build_leave_room(user, room))

    def send_group(self, user: str, room: str, msg: str, file_path: str = None) -> bool:
        """Gửi tin nhắn nhóm, có thể kèm file"""
        file_data = None
        if file_path:
            file_data = encode_file(file_path)
            if not file_data:
                print(f"Failed to encode file: {file_path}")
                return False
        
        return self.send_raw(build_group(room, user, msg, file_data))

    # ===== Receive =====
    def _recv_loop(self):
        buffer = b""
        try:
            while self.running and self.connected:
                chunk = self.socket.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line:
                        continue
                    data = decode_message(line)
                    if data is not None and self.on_message:
                        self.on_message(data)
        except Exception as e:
            print(f"Receive error: {e}")
        self._handle_disconnect()

    def _handle_disconnect(self):
        if self.connected:
            self.connected = False
            self.running = False
            if self.on_disconnect:
                self.on_disconnect()