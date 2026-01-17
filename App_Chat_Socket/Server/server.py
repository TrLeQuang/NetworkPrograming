import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

from server_handler import ClientHandler
from user_manager import UserManager

# Task 5 (log file)
from chat_logger import ChatLogger


class ChatServerGUI:
    def __init__(self, host="127.0.0.1", port=5555):
        self.host = host
        self.port = port
        self.server = None

        # list handler = số connection socket đang connect
        self.clients = []
        self.client_lock = threading.Lock()
        self.running = False

        # user_manager = số user đã login thành công
        self.user_manager = UserManager()

        # file logger (Task 5)
        self.file_logger = ChatLogger()

        # Tạo GUI
        self.window = tk.Tk()
        self.window.title("Chat Server Dashboard")
        self.window.geometry("700x600")
        self.window.config(bg="#1e1e2e")

        self.setup_gui()

    def setup_gui(self):
        """Thiết lập giao diện server"""
        header_frame = tk.Frame(self.window, bg="#89b4fa", height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🖥️ CHAT SERVER DASHBOARD",
            font=("Arial", 16, "bold"),
            bg="#89b4fa",
            fg="#1e1e2e",
        )
        title_label.pack(pady=15)

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

        log_label = tk.Label(
            self.window,
            text="📋 Server Logs",
            font=("Arial", 10, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4",
            anchor="w",
        )
        log_label.pack(fill=tk.X, padx=20, pady=(10, 5))

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

    def log(self, message: str, level: str = "INFO"):
        """Ghi log vào text area + file log"""
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
        self.log_area.tag_config(
            level,
            foreground=colors.get(level, "#cdd6f4"),
            font=("Consolas", 9, "bold"),
        )

        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

        # Task 5: log ra file
        try:
            self.file_logger.write(level, message)
        except:
            pass

    # ====== COUNT / REFRESH ======
    def update_client_count(self):
        """Update label: Online users + Socket connections"""
        with self.client_lock:
            connections = len(self.clients)
        try:
            online = len(self.user_manager.get_online_users())
        except:
            online = 0

        self.clients_label.config(text=f"👥 Online: {online} | Connect: {connections}")

    def refresh_online_count(self):
        """Gọi từ handler sau login/logout để refresh UI"""
        self.update_client_count()

    # ====== SERVER CORE ======
    def start_server(self):
        """Khởi động server"""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            self.running = True

            self.status_label.config(
                text=f"● Server: ONLINE @ {self.host}:{self.port}", fg="#a6e3a1"
            )
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

            self.log(f"Server đang chạy trên {self.host}:{self.port}", "SUCCESS")
            self.log("Đang chờ kết nối từ clients...", "INFO")

            accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
            accept_thread.start()

        except Exception as e:
            self.log(f"Lỗi khi khởi động server: {e}", "ERROR")

    def accept_connections(self):
        """Accept nhiều client connections"""
        while self.running:
            try:
                client_socket, address = self.server.accept()
                self.log(f"Kết nối mới từ {address[0]}:{address[1]}", "CLIENT")

                handler = ClientHandler(client_socket, address, self, self.user_manager)

                with self.client_lock:
                    self.clients.append(handler)
                self.update_client_count()

                handler.start()

            except Exception as e:
                if self.running:
                    self.log(f"Lỗi khi accept connection: {e}", "ERROR")
                break

    def broadcast(self, data: dict, exclude_username: str | None = None):
        """Gửi message (Protocol JSON) đến tất cả clients đã login."""
        online_users = self.user_manager.get_online_users()

        for username in online_users:
            if exclude_username and username == exclude_username:
                continue

            handler = self.user_manager.get_handler(username)
            if handler:
                try:
                    handler.send_raw(data)
                except Exception as e:
                    self.log(f"Không thể gửi tới {username}: {e}", "ERROR")

    def remove_client(self, handler):
        """Xóa handler khỏi list connection khi disconnect"""
        with self.client_lock:
            if handler in self.clients:
                self.clients.remove(handler)
        self.update_client_count()

    def stop_server(self):
        """Tắt server"""
        self.log("Đang tắt server...", "WARNING")
        self.running = False

        with self.client_lock:
            for handler in self.clients[:]:
                try:
                    handler.close()
                except:
                    pass

        if self.server:
            try:
                self.server.close()
            except:
                pass

        self.status_label.config(text="● Server: OFFLINE", fg="#f38ba8")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.update_client_count()

        self.log("Server đã tắt", "INFO")

    def on_closing(self):
        """Xử lý khi đóng cửa sổ"""
        if self.running:
            self.stop_server()
        self.window.destroy()

    def run(self):
        """Chạy ứng dụng"""
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log("Chat Server Dashboard khởi động", "SUCCESS")
        self.log(f"Sẵn sàng khởi động server tại {self.host}:{self.port}", "INFO")
        self.window.mainloop()


if __name__ == "__main__":
    server_gui = ChatServerGUI()
    server_gui.run()
