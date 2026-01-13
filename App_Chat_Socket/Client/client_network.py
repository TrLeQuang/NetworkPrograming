import socket
import threading
import time
from typing import Callable, Optional

# Import protocol từ Server
from protocol import encode_message, decode_message, build_login, build_logout


class ClientNetwork:
    """
    Quản lý kết nối socket client.
    Gửi/nhận message, xử lý reconnect, error handling.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5555):
        self.host = host
        self. port = port
        self.socket:  Optional[socket.socket] = None
        self.connected = False
        self.running = False
        
        # Thread nhận dữ liệu
        self.receive_thread: Optional[threading.Thread] = None
        
        # Callback để xử lý message nhận được
        self.on_message_callback: Optional[Callable] = None
        self.on_disconnect_callback: Optional[Callable] = None

    def set_on_message(self, callback: Callable):
        """
        Đăng ký callback để xử lý message nhận từ server.
        callback(data: dict)
        """
        self.on_message_callback = callback

    def set_on_disconnect(self, callback: Callable):
        """
        Đăng ký callback khi bị disconnect.
        callback()
        """
        self. on_disconnect_callback = callback

    def connect(self) -> bool:
        """
        Kết nối tới server. 
        Trả về True nếu thành công. 
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket. connect((self.host, self. port))
            self.connected = True
            self.running = True
            
            # Khởi động thread nhận dữ liệu
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread. start()
            
            print(f"[CLIENT] Đã kết nối tới {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[CLIENT] Lỗi kết nối:  {e}")
            self.connected = False
            return False

    def disconnect(self):
        """
        Ngắt kết nối và dừng thread nhận. 
        """
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("[CLIENT] Đã ngắt kết nối")

    def send_raw(self, data: dict) -> bool:
        """
        Gửi raw dict data lên server (đã encode thành bytes).
        Trả về True nếu gửi thành công.
        """
        if not self.connected or not self.socket:
            print("[CLIENT] Không thể gửi, chưa kết nối")
            return False
        
        try:
            raw_bytes = encode_message(data)
            # Thêm \n để server biết kết thúc message
            self.socket.sendall(raw_bytes + b'\n')
            return True
        except Exception as e:
            print(f"[CLIENT] Lỗi gửi message: {e}")
            self._handle_disconnect()
            return False

    def send_login(self, username: str) -> bool:
        """
        Gửi gói login lên server.
        Sử dụng build_login từ protocol.
        """
        data = build_login(username)
        return self.send_raw(data)

    def send_logout(self, username: str) -> bool:
        """
        Gửi gói logout lên server.
        Sử dụng build_logout từ protocol.
        """
        data = build_logout(username)
        return self.send_raw(data)

    def send_message(self, username: str, msg:  str) -> bool:
        """
        Gửi message chat lên server.
        Client gửi:  {"type": "message", "user": "A", "msg": "hello"}
        """
        data = {
            "type": "message",
            "user": username,
            "msg": msg
        }
        return self.send_raw(data)

    def _receive_loop(self):
        """
        Thread nhận dữ liệu liên tục từ server.
        Xử lý message phân tách bằng \n
        """
        buffer = b""
        
        while self.running and self.connected:
            try:
                chunk = self.socket.recv(4096)
                if not chunk: 
                    # Server đóng kết nối
                    print("[CLIENT] Server đã đóng kết nối")
                    self._handle_disconnect()
                    break
                
                buffer += chunk
                
                # Xử lý message (mỗi message kết thúc bằng \n)
                while b'\n' in buffer: 
                    line, buffer = buffer.split(b'\n', 1)
                    if line:  # Bỏ qua dòng trống
                        self._process_message(line)
                
            except Exception as e:
                if self.running:
                    print(f"[CLIENT] Lỗi nhận dữ liệu: {e}")
                self._handle_disconnect()
                break

    def _process_message(self, raw:  bytes):
        """
        Xử lý message nhận được từ server.
        """
        data = decode_message(raw)
        if data is None:
            print("[CLIENT] Nhận được message không hợp lệ")
            return
        
        # Gọi callback nếu có
        if self.on_message_callback:
            self. on_message_callback(data)

    def _handle_disconnect(self):
        """
        Xử lý khi bị disconnect.
        """
        self.connected = False
        self.running = False
        
        # Gọi callback nếu có
        if self. on_disconnect_callback:
            self.on_disconnect_callback()

    def reconnect(self) -> bool:
        """
        Thử reconnect lại server.
        """
        print("[CLIENT] Đang thử reconnect...")
        self.disconnect()
        time.sleep(2)
        return self.connect()