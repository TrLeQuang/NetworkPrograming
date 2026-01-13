import threading
from protocol import (
    encode_message,
    decode_message,
    build_chat_message,
    build_system_message,
    build_user_list,
    build_error
)


class ClientHandler(threading.Thread):
    """
    Xử lý kết nối của từng client. 
    Thread riêng cho mỗi client.
    Tương thích với Protocol JSON.
    """
    
    def __init__(self, client_socket, address, server, user_manager):
        super().__init__()
        self.client_socket = client_socket
        self. address = address
        self.server = server
        self.user_manager = user_manager
        self.username = None
        self.running = True
        
    def run(self):
        """Thread chính xử lý client"""
        try:
            # Buffer để xử lý message
            buffer = b""
            
            # Nhận và xử lý messages
            while self.running:
                try:
                    chunk = self.client_socket.recv(4096)
                    
                    if not chunk:
                        # Client đã disconnect
                        break
                    
                    buffer += chunk
                    
                    # Xử lý messages (phân tách bằng \n)
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        if line: 
                            self._process_message(line)
                        
                except Exception as e:
                    self.server.log(f"Lỗi khi nhận message từ {self.username or self.address}: {e}", "ERROR")
                    break
                    
        except Exception as e: 
            self.server.log(f"Lỗi với client {self.address}: {e}", "ERROR")
        
        finally:
            self.close()
    
    def _process_message(self, raw:  bytes):
        """
        Xử lý message nhận được từ client.
        """
        data = decode_message(raw)
        
        if data is None:
            self.server.log(f"Message không hợp lệ từ {self.username or self. address}", "WARNING")
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
    
    def _handle_login(self, data:  dict):
        """
        Xử lý login. 
        Format: {"type": "login", "user": "A"}
        """
        username = data.get("user", "").strip()
        
        if not username:
            error_msg = build_error("Username không hợp lệ")
            self.send_raw(error_msg)
            return
        
        # Kiểm tra username đã tồn tại chưa
        if self.user_manager.has_user(username):
            error_msg = build_error("Username đã tồn tại, vui lòng chọn tên khác")
            self.send_raw(error_msg)
            self.server.log(f"❌ Login thất bại: '{username}' đã tồn tại", "WARNING")
            return
        
        # Thêm user vào danh sách
        self. username = username
        self.user_manager.add_user(username, self)
        
        self.server.log(f"✅ User '{username}' đã login từ {self.address[0]}:{self.address[1]}", "SUCCESS")
        
        # Gửi system message cho tất cả
        system_msg = build_system_message(f"{username} đã tham gia phòng chat")
        self.server.broadcast(system_msg)
        
        # Gửi danh sách user online cho tất cả
        self._broadcast_user_list()
    
    def _handle_logout(self, data: dict):
        """
        Xử lý logout.
        Format: {"type":  "logout", "user": "A"}
        """
        username = data.get("user", "")
        self.server.log(f"👋 User '{username}' đã logout", "INFO")
        self.running = False
    
    def _handle_chat_message(self, data: dict):
        """
        Xử lý chat message từ client.
        Client gửi:  {"type": "message", "user": "A", "msg": "hello"}
        Server broadcast: {"type": "message", "from": "A", "msg": "hello", "timestamp": "... "}
        """
        username = data.get("user", "Unknown")
        msg = data.get("msg", "")
        
        if not msg. strip():
            return
        
        self.server.log(f"💬 {username}: {msg}", "CLIENT")
        
        # Build message theo protocol
        chat_msg = build_chat_message(username, msg)
        
        # Broadcast đến tất cả clients (bao gồm cả người gửi)
        self.server.broadcast(chat_msg)
    
    def send_raw(self, data: dict):
        """
        Gửi raw dict data đến client (đã encode thành bytes).
        Thêm \n để đánh dấu kết thúc message.
        """
        try:
            raw_bytes = encode_message(data)
            # QUAN TRỌNG: Thêm \n để client biết kết thúc message
            self.client_socket. sendall(raw_bytes + b'\n')
        except Exception as e:
            self.server.log(f"Không thể gửi message đến {self.username}:  {e}", "ERROR")
            self.running = False
    
    def send_message(self, message):
        """
        (Deprecated) Giữ lại để tương thích với code cũ.
        Chuyển đổi string message sang Protocol JSON.
        """
        # Parse message để xác định type
        if message.startswith("[SERVER]"):
            # System message
            msg = message. replace("[SERVER]", "").strip()
            data = build_system_message(msg)
        else:
            # Giả sử là chat message từ broadcast cũ
            # Format: "username: message"
            parts = message.split(":", 1)
            if len(parts) == 2:
                username = parts[0].strip()
                msg = parts[1]. strip()
                data = build_chat_message(username, msg)
            else:
                # Fallback:  system message
                data = build_system_message(message)
        
        self.send_raw(data)
    
    def _broadcast_user_list(self):
        """
        Broadcast danh sách user online cho tất cả clients.
        """
        online_users = self.user_manager.get_online_users()
        user_list_msg = build_user_list(online_users)
        self.server.broadcast(user_list_msg)
    
    def close(self):
        """Đóng kết nối và cleanup"""
        self.running = False
        
        if self.username:
            # Xóa user khỏi danh sách
            self.user_manager.remove_user(self.username)
            
            # Thông báo user rời khỏi
            leave_msg = build_system_message(f"{self.username} đã rời khỏi phòng chat")
            self.server.log(f"👋 User '{self.username}' đã rời khỏi", "WARNING")
            self.server.broadcast(leave_msg)
            
            # Cập nhật danh sách user online
            self._broadcast_user_list()
        
        # Xóa khỏi danh sách clients
        self.server.remove_client(self)
        
        # Đóng socket
        try:
            self.client_socket.close()
        except:
            pass