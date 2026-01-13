import sys
import threading
from client_network import ClientNetwork


class ChatClient:
    """
    Client chat console đơn giản. 
    Dùng để test, chưa có UI. 
    """

    def __init__(self):
        self.network = ClientNetwork()
        self.username = ""
        self.running = False

    def start(self):
        """Khởi động client."""
        print("=" * 50)
        print(" " * 15 + "CHAT CLIENT")
        print("=" * 50)
        
        # Nhập username
        self.username = input("Nhập username của bạn: ").strip()
        if not self.username:
            print("❌ Username không hợp lệ!")
            return

        # Kết nối tới server
        self.network.set_on_message(self. on_message)
        self.network.set_on_disconnect(self.on_disconnect)
        
        if not self.network. connect():
            print("❌ Không thể kết nối tới server!")
            return

        # Gửi login
        print(f"📤 Đang login với username: {self.username}")
        self.network.send_login(self.username)
        
        self.running = True
        
        # Thread nhập message
        input_thread = threading.Thread(target=self.input_loop, daemon=True)
        input_thread.start()

        # Giữ main thread chạy
        try:
            while self.running:
                threading.Event().wait(1)
        except KeyboardInterrupt: 
            self.stop()

    def stop(self):
        """Dừng client."""
        print("\n[CLIENT] Đang thoát...")
        self.running = False
        self.network. send_logout(self.username)
        self.network.disconnect()
        sys.exit(0)

    def input_loop(self):
        """Thread nhập message từ console."""
        print("\n" + "=" * 50)
        print("💬 Bạn có thể gửi message")
        print("⌨️  Gõ 'quit' hoặc 'exit' để thoát")
        print("=" * 50 + "\n")
        
        while self.running:
            try:
                msg = input()
                
                if msg.lower() in ['quit', 'exit']:
                    self.stop()
                    break
                
                if msg. strip():
                    self.network. send_message(self.username, msg)
            except: 
                break

    def on_message(self, data: dict):
        """
        Callback xử lý message nhận từ server.
        Xử lý theo protocol đã định nghĩa.
        """
        msg_type = data.get("type")
        
        if msg_type == "message":
            # Message chat từ user khác
            # Format: {"type": "message", "from": "A", "msg": "hi", "timestamp": "... "}
            sender = data.get("from", "Unknown")
            msg = data.get("msg", "")
            timestamp = data.get("timestamp", "")
            print(f"[{timestamp}] {sender}: {msg}")
        
        elif msg_type == "system":
            # System message (join/leave)
            # Format: {"type": "system", "msg": "A đã tham gia", "timestamp": "..."}
            msg = data.get("msg", "")
            timestamp = data. get("timestamp", "")
            print(f"[{timestamp}] 🔔 {msg}")
        
        elif msg_type == "user_list":
            # Danh sách user online
            # Format: {"type": "user_list", "users": ["A", "B"]}
            users = data.get("users", [])
            print(f"\n👥 User online ({len(users)}): {', '.join(users)}\n")
        
        elif msg_type == "error":
            # Lỗi từ server
            # Format: {"type": "error", "msg": "Username đã tồn tại"}
            msg = data.get("msg", "")
            print(f"\n❌ LỖI: {msg}\n")
            # Nếu lỗi login, thoát
            if "tồn tại" in msg. lower() or "exist" in msg.lower():
                print("Vui lòng khởi động lại với username khác!")
                self.stop()
        
        else:
            # Message type không xác định
            print(f"[DEBUG] Nhận message không xác định: {data}")

    def on_disconnect(self):
        """
        Callback khi bị disconnect.
        """
        print("\n" + "=" * 50)
        print("⚠️  MẤT KẾT NỐI VỚI SERVER")
        print("=" * 50)
        
        # Hỏi user có muốn reconnect không
        try:
            retry = input("🔄 Bạn có muốn thử kết nối lại?  (y/n): ").strip().lower()
            if retry == 'y':
                if self.network.reconnect():
                    print("✅ Reconnect thành công!")
                    # Gửi lại login
                    self.network.send_login(self.username)
                else:
                    print("❌ Reconnect thất bại!")
                    self.stop()
            else:
                self.stop()
        except:
            self.stop()


if __name__ == "__main__": 
    client = ChatClient()
    client.start()