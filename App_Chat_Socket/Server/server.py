"""
Chat Server với GUI Tkinter
Dashboard đẹp để quản lý server
"""

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
from typing import Optional

from user_manager import UserManager
from room_manager import RoomManager
from logger import ChatLogger
from protocol import (
    encode_message, decode_message,
    build_user_list, build_system, build_error,
    build_private, build_group, build_room_list
)


class ClientHandler(threading.Thread):
    def __init__(self, conn: socket.socket, addr, server):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.server = server
        self.username: Optional[str] = None
        self.running = True

    def run(self):
        buffer = b""
        try:
            while self.running:
                chunk = self.conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line:
                        continue
                    data = decode_message(line)
                    if data:
                        self.handle_message(data)
        except Exception as e:
            self.server.log(f"Error từ {self.addr}: {e}", "ERROR")
        finally:
            self.disconnect()

    def handle_message(self, data: dict):
        t = data.get("type")

        if t == "login":
            user = data.get("user", "").strip()
            if not user:
                self.send_raw(build_error("Username không hợp lệ"))
                return
            if self.server.user_manager.has_user(user):
                self.send_raw(build_error(f"Username '{user}' đã được sử dụng"))
                return
            
            self.username = user
            self.server.user_manager.add_user(user, self)
            self.server.logger.write("INFO", f"{user} login từ {self.addr}")
            self.server.log(f"✓ {user} đã login từ {self.addr[0]}:{self.addr[1]}", "SUCCESS")
            
            self.server.send_user_list_all()
            self.server.send_room_list_all()
            self.send_raw(build_system(f"Chào mừng {user}!"))

        elif t == "logout":
            self.disconnect()

        elif t == "private":
            sender = data.get("from", "").strip()
            to_user = data.get("to", "").strip()
            msg = data.get("msg", "")
            file_data = data.get("file")

            if sender != self.username:
                self.send_raw(build_error("Sender không khớp"))
                return
            
            target = self.server.user_manager.get_handler(to_user)
            if not target:
                self.send_raw(build_error(f"User '{to_user}' không online"))
                return
            
            private_msg = build_private(sender, to_user, msg, file_data)
            target.send_raw(private_msg)
            self.send_raw(private_msg)
            
            log_msg = f"{sender} → {to_user}: {msg[:30] if msg else ''}"
            if file_data:
                log_msg += f" [📎 {file_data.get('name')}]"
            self.server.log(log_msg, "CLIENT")
            self.server.logger.write("PRIVATE", log_msg)

        elif t == "create_room":
            user = data.get("user", "").strip()
            room = data.get("room", "").strip()
            if user != self.username:
                return
            if not room:
                self.send_raw(build_error("Tên phòng không hợp lệ"))
                return
            if self.server.room_manager.create_room(room):
                self.server.send_room_list_all()
                self.server.broadcast_room(room, build_system(f"{user} đã tạo phòng '{room}'", room))
                self.server.log(f"🏠 {user} tạo phòng '{room}'", "SUCCESS")
                self.server.logger.write("ROOM", f"{user} tạo phòng '{room}'")
            else:
                self.send_raw(build_error(f"Phòng '{room}' đã tồn tại"))

        elif t == "join_room":
            user = data.get("user", "").strip()
            room = data.get("room", "").strip()
            if user != self.username:
                return
            if not self.server.room_manager.room_exists(room):
                self.send_raw(build_error(f"Phòng '{room}' không tồn tại"))
                return
            if self.server.room_manager.join(room, user):
                self.server.send_room_list_all()
                self.server.broadcast_room(room, build_system(f"{user} đã join phòng '{room}'", room))
                self.server.log(f"👥 {user} join phòng '{room}'", "INFO")
                self.server.logger.write("ROOM", f"{user} join phòng '{room}'")

        elif t == "leave_room":
            user = data.get("user", "").strip()
            room = data.get("room", "").strip()
            if user != self.username:
                return
            if self.server.room_manager.leave(room, user):
                self.server.send_room_list_all()
                self.server.broadcast_room(room, build_system(f"{user} đã rời phòng '{room}'", room))
                self.server.log(f"👋 {user} rời phòng '{room}'", "WARNING")
                self.server.logger.write("ROOM", f"{user} rời phòng '{room}'")

        elif t == "group":
            room = data.get("room", "").strip()
            sender = data.get("from", "").strip()
            msg = data.get("msg", "")
            file_data = data.get("file")

            if sender != self.username:
                self.send_raw(build_error("Sender không khớp"))
                return
            
            members = self.server.room_manager.members(room)
            if sender not in members:
                self.send_raw(build_error(f"Bạn chưa join phòng '{room}'"))
                return
            
            group_msg = build_group(room, sender, msg, file_data)
            self.server.broadcast_room(room, group_msg)
            
            log_msg = f"[{room}] {sender}: {msg[:30] if msg else ''}"
            if file_data:
                log_msg += f" [📎 {file_data.get('name')}]"
            self.server.log(log_msg, "CLIENT")
            self.server.logger.write("GROUP", log_msg)

    def send_raw(self, data: dict):
        try:
            self.conn.sendall(encode_message(data) + b"\n")
        except Exception as e:
            self.server.log(f"Lỗi gửi đến {self.addr}: {e}", "ERROR")

    def disconnect(self):
        if self.username:
            self.server.user_manager.remove_user(self.username)
            self.server.room_manager.remove_user_everywhere(self.username)
            self.server.logger.write("INFO", f"{self.username} logout")
            self.server.log(f"✗ {self.username} đã logout", "WARNING")
            self.server.send_user_list_all()
            self.server.send_room_list_all()
        
        self.server.remove_client(self)
        
        try:
            self.conn.close()
        except Exception:
            pass
        self.running = False


class ChatServerGUI:
    def __init__(self, host="0.0.0.0", port=5555):
        self.host = host
        self.port = port

        self.server_socket = None
        self.running = False

        self.clients = []
        self.client_lock = threading.Lock()

        self.user_manager = UserManager()
        self.room_manager = RoomManager()
        self.logger = ChatLogger()

        # GUI
        self.window = tk.Tk()
        self.window.title("Chat Server Dashboard")
        self.window.geometry("700x600")
        self.window.config(bg="#1e1e2e")

        self.setup_gui()

    def setup_gui(self):
        # Header
        header_frame = tk.Frame(self.window, bg="#89b4fa", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        tk.Label(
            header_frame,
            text="🖥️ CHAT SERVER DASHBOARD",
            font=("Arial", 16, "bold"),
            bg="#89b4fa",
            fg="#1e1e2e",
        ).pack(pady=15)

        # Info frame
        info_frame = tk.Frame(self.window, bg="#1e1e2e")
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        self.status_label = tk.Label(
            info_frame,
            text="● Server: OFFLINE",
            font=("Arial", 11, "bold"),
            bg="#1e1e2e",
            fg="#f38ba8",
        )
        self.status_label.pack(side=tk.LEFT)

        self.clients_label = tk.Label(
            info_frame,
            text="👥 Online: 0 | Conn: 0",
            font=("Arial", 11),
            bg="#1e1e2e",
            fg="#a6e3a1",
        )
        self.clients_label.pack(side=tk.RIGHT)

        # Log area
        tk.Label(
            self.window,
            text="📋 Server Logs",
            font=("Arial", 10, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4",
            anchor="w",
        ).pack(fill=tk.X, padx=20, pady=(10, 5))

        self.log_area = scrolledtext.ScrolledText(
            self.window,
            wrap=tk.WORD,
            state="disabled",
            height=20,
            font=("Consolas", 9),
            bg="#313244",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            relief=tk.FLAT,
        )
        self.log_area.pack(padx=20, pady=(0, 10), fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = tk.Frame(self.window, bg="#1e1e2e")
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.start_button = tk.Button(
            button_frame,
            text="▶ START SERVER",
            command=self.start_server,
            bg="#a6e3a1",
            fg="#1e1e2e",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10,
        )
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.stop_button = tk.Button(
            button_frame,
            text="⬛ STOP SERVER",
            command=self.stop_server,
            bg="#f38ba8",
            fg="#1e1e2e",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10,
            state="disabled",
        )
        self.stop_button.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    def log(self, message: str, level="INFO"):
        """Hiển thị log trong GUI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "#89b4fa",
            "SUCCESS": "#a6e3a1",
            "WARNING": "#f9e2af",
            "ERROR": "#f38ba8",
            "CLIENT": "#cba6f7",
        }

        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_area.insert(tk.END, f"[{level}] ", level)
        self.log_area.insert(tk.END, f"{message}\n")
        self.log_area.tag_config("timestamp", foreground="#6c7086")
        self.log_area.tag_config(level, foreground=colors.get(level, "#cdd6f4"), font=("Consolas", 9, "bold"))
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def update_counts(self):
        """Cập nhật số lượng users và connections"""
        with self.client_lock:
            conn = len(self.clients)
        online = len(self.user_manager.get_online_users())
        self.clients_label.config(text=f"👥 Online: {online} | Conn: {conn}")

    def start_server(self):
        """Khởi động server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            self.status_label.config(text=f"● Server: ONLINE @ {self.host}:{self.port}", fg="#a6e3a1")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

            self.log(f"Server đang chạy trên {self.host}:{self.port}", "SUCCESS")
            self.log(f"Log file: {self.logger.file_path}", "INFO")
            self.log("Đang chờ kết nối từ clients...", "INFO")

            self.logger.write("INFO", f"Server khởi động tại {self.host}:{self.port}")

            threading.Thread(target=self.accept_loop, daemon=True).start()
        except Exception as e:
            self.log(f"Lỗi khi khởi động server: {e}", "ERROR")

    def accept_loop(self):
        """Vòng lặp chấp nhận kết nối"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                self.log(f"🔌 Kết nối mới từ {address[0]}:{address[1]}", "CLIENT")

                handler = ClientHandler(client_socket, address, self)

                with self.client_lock:
                    self.clients.append(handler)
                self.update_counts()

                handler.start()
            except Exception as e:
                if self.running:
                    self.log(f"Lỗi accept: {e}", "ERROR")
                break

    # ===== Broadcast helpers =====
    def broadcast_online(self, data: dict, exclude: str | None = None):
        """Gửi message đến tất cả users online"""
        for u in self.user_manager.get_online_users():
            if exclude and u == exclude:
                continue
            h = self.user_manager.get_handler(u)
            if h:
                try:
                    h.send_raw(data)
                except Exception:
                    pass

    def send_user_list_all(self):
        """Gửi danh sách users đến tất cả clients"""
        self.broadcast_online(build_user_list(self.user_manager.get_online_users()))
        self.update_counts()

    def send_room_list_all(self):
        """Gửi danh sách rooms đến tất cả clients"""
        self.broadcast_online(build_room_list(self.room_manager.snapshot()))

    def broadcast_system(self, msg: str):
        """Broadcast system message"""
        self.broadcast_online(build_system(msg))

    def broadcast_room(self, room: str, data: dict):
        """Gửi message đến tất cả members trong room"""
        members = self.room_manager.members(room)
        for u in members:
            h = self.user_manager.get_handler(u)
            if h:
                try:
                    h.send_raw(data)
                except Exception:
                    pass

    def remove_client(self, handler):
        """Xóa client khỏi danh sách"""
        with self.client_lock:
            if handler in self.clients:
                self.clients.remove(handler)
        self.update_counts()

    def stop_server(self):
        """Tắt server"""
        self.log("Đang tắt server...", "WARNING")
        self.running = False

        # Đóng tất cả connections
        with self.client_lock:
            for h in self.clients[:]:
                try:
                    h.running = False
                    h.conn.close()
                except Exception:
                    pass

        # Đóng server socket
        try:
            if self.server_socket:
                self.server_socket.close()
        except Exception:
            pass

        self.status_label.config(text="● Server: OFFLINE", fg="#f38ba8")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.update_counts()
        self.log("Server đã tắt", "SUCCESS")
        self.logger.write("INFO", "Server đã tắt")

    def on_close(self):
        """Xử lý khi đóng cửa sổ"""
        if self.running:
            self.stop_server()
        self.window.destroy()

    def run(self):
        """Chạy GUI"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.log("🚀 Dashboard khởi động", "SUCCESS")
        self.window.mainloop()


if __name__ == "__main__":
    ChatServerGUI().run()