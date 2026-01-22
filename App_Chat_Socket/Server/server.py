import os
import sys
import importlib.util

# Đảm bảo Python luôn import được các file trong thư mục Server (không cần set Working Directory)
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

from server_handler import ClientHandler
from user_manager import UserManager
from room_manager import RoomManager

# =========================
# Load protocol.py kiểu "đường dẫn tuyệt đối" (VS2022-safe)
# =========================
PROTOCOL_PATH = os.path.join(THIS_DIR, "protocol.py")
if not os.path.exists(PROTOCOL_PATH):
    raise FileNotFoundError(f"Không tìm thấy protocol.py tại: {PROTOCOL_PATH}")

_spec = importlib.util.spec_from_file_location("server_protocol", PROTOCOL_PATH)
_protocol = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_protocol)

# =========================
# Bind đúng tên hàm theo protocol.py hiện tại
# =========================
build_system = _protocol.build_system
build_user_list = _protocol.build_user_list
build_room_list = _protocol.build_room_list




class ChatServerGUI:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port

        self.server = None
        self.running = False

        self.clients = []  # connection handlers
        self.client_lock = threading.Lock()

        self.user_manager = UserManager()   # online users
        self.room_manager = RoomManager()   # rooms

        # GUI
        self.window = tk.Tk()
        self.window.title("Chat Server Dashboard")
        self.window.geometry("700x600")
        self.window.config(bg="#1e1e2e")

        self.setup_gui()

    def setup_gui(self):
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
        with self.client_lock:
            conn = len(self.clients)
        online = len(self.user_manager.get_online_users())
        self.clients_label.config(text=f"👥 Online: {online} | Conn: {conn}")

    def start_server(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            self.running = True

            self.status_label.config(text=f"● Server: ONLINE @ {self.host}:{self.port}", fg="#a6e3a1")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

            self.log(f"Server đang chạy trên {self.host}:{self.port}", "SUCCESS")
            self.log("Đang chờ kết nối từ clients...", "INFO")

            threading.Thread(target=self.accept_loop, daemon=True).start()
        except Exception as e:
            self.log(f"Lỗi khi khởi động server: {e}", "ERROR")

    def accept_loop(self):
        while self.running:
            try:
                client_socket, address = self.server.accept()
                self.log(f"Kết nối mới từ {address[0]}:{address[1]}", "CLIENT")

                handler = ClientHandler(client_socket, address, self, self.user_manager)

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
        self.broadcast_online(build_user_list(self.user_manager.get_online_users()))

    def send_room_list_all(self):
        self.broadcast_online(build_room_list(self.room_manager.snapshot()))

    def broadcast_system(self, msg: str):
        self.broadcast_online(build_system(msg))

    def broadcast_room(self, room: str, data: dict):
        members = self.room_manager.members(room)
        for u in members:
            h = self.user_manager.get_handler(u)
            if h:
                try:
                    h.send_raw(data)
                except Exception:
                    pass

    def remove_client(self, handler):
        with self.client_lock:
            if handler in self.clients:
                self.clients.remove(handler)
        self.update_counts()

    def stop_server(self):
        self.log("Đang tắt server...", "WARNING")
        self.running = False

        with self.client_lock:
            for h in self.clients[:]:
                try:
                    h.close()
                except Exception:
                    pass

        try:
            if self.server:
                self.server.close()
        except Exception:
            pass

        self.status_label.config(text="● Server: OFFLINE", fg="#f38ba8")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.update_counts()
        self.log("Server đã tắt", "INFO")

    def on_close(self):
        if self.running:
            self.stop_server()
        self.window.destroy()

    def run(self):
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.log("Dashboard khởi động", "SUCCESS")
        self.window.mainloop()


if __name__ == "__main__":
    ChatServerGUI().run()
