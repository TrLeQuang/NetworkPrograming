import socket
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

from Config import SERVER_IP, SERVER_PORT
from Reliable_UDP import ReliableUDP


class ChatClientGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("UDP Chat - Demo tối ưu UDP (GUI)")
        self.root.geometry("820x520")
        self.root.minsize(760, 480)

        self.server_addr = (SERVER_IP, SERVER_PORT)

        # Hàng đợi để thread nhận tin nhắn đẩy vào (tránh đụng Tkinter từ thread khác)
        self.inbox = queue.Queue()

        self.sock = None
        self.rudp = None
        self.recv_thread = None

        self.connected = False
        self.name = ""

        self._build_ui()
        self._poll_inbox()  # vòng lặp kiểm tra inbox để cập nhật UI

        # Khi đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- UI ----------------
    def _build_ui(self):
        # Layout chính: trái (info) - phải (chat)
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=3)
        container.rowconfigure(0, weight=1)

        # Panel trái
        left = ttk.Frame(container)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Panel phải
        right = ttk.Frame(container)
        right.grid(row=0, column=1, sticky="nsew")

        # --------- LEFT: Thông tin + cấu hình ----------
        info_card = ttk.LabelFrame(left, text="Thông tin kết nối", padding=10)
        info_card.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(info_card, text="Tên của bạn:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(info_card, textvariable=self.name_var)
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(4, 8))

        ttk.Label(info_card, text="Server IP:").grid(row=2, column=0, sticky="w")
        self.ip_var = tk.StringVar(value=SERVER_IP)
        self.ip_entry = ttk.Entry(info_card, textvariable=self.ip_var)
        self.ip_entry.grid(row=3, column=0, sticky="ew", pady=(4, 8))

        ttk.Label(info_card, text="Server Port:").grid(row=4, column=0, sticky="w")
        self.port_var = tk.StringVar(value=str(SERVER_PORT))
        self.port_entry = ttk.Entry(info_card, textvariable=self.port_var)
        self.port_entry.grid(row=5, column=0, sticky="ew", pady=(4, 10))

        info_card.columnconfigure(0, weight=1)

        btn_row = ttk.Frame(info_card)
        btn_row.grid(row=6, column=0, sticky="ew")
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        self.connect_btn = ttk.Button(btn_row, text="Kết nối", command=self.connect)
        self.connect_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.disconnect_btn = ttk.Button(btn_row, text="Ngắt kết nối", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.status_var = tk.StringVar(value="Trạng thái: Chưa kết nối")
        status_card = ttk.LabelFrame(left, text="Trạng thái", padding=10)
        status_card.pack(fill=tk.X)

        self.status_label = ttk.Label(status_card, textvariable=self.status_var, wraplength=240, justify="left")
        self.status_label.pack(fill=tk.X)

        note = ttk.Label(
            left,
            text="Gợi ý:\n- Mở chat_server.py trước\n- Có thể mở nhiều client GUI\n- UDP sẽ giả lập mất gói và tự resend",
            justify="left"
        )
        note.pack(fill=tk.X, pady=(10, 0))

        # --------- RIGHT: Chat view ----------
        chat_card = ttk.LabelFrame(right, text="Phòng chat", padding=10)
        chat_card.pack(fill=tk.BOTH, expand=True)

        chat_card.columnconfigure(0, weight=1)
        chat_card.rowconfigure(0, weight=1)

        # Text box + scrollbar
        self.chat_text = tk.Text(chat_card, wrap="word", state="disabled")
        self.chat_text.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(chat_card, orient="vertical", command=self.chat_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.chat_text.configure(yscrollcommand=scroll.set)

        # Khung nhập tin nhắn
        input_row = ttk.Frame(chat_card)
        input_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        input_row.columnconfigure(0, weight=1)

        self.msg_var = tk.StringVar()
        self.msg_entry = ttk.Entry(input_row, textvariable=self.msg_var)
        self.msg_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.send_btn = ttk.Button(input_row, text="Gửi", command=self.send_message, state=tk.DISABLED)
        self.send_btn.grid(row=0, column=1)

        # Bắt Enter để gửi
        self.msg_entry.bind("<Return>", lambda e: self.send_message())

        # Focus ban đầu
        self.name_entry.focus_set()

    # ---------------- Helpers ----------------
    def _append_chat(self, line: str):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", line + "\n")
        self.chat_text.see("end")
        self.chat_text.configure(state="disabled")

    def _set_status(self, text: str):
        self.status_var.set("Trạng thái: " + text)

    def _poll_inbox(self):
        """Lấy tin nhắn từ queue (do thread nhận đẩy vào) để cập nhật UI."""
        try:
            while True:
                sender, text = self.inbox.get_nowait()
                self._append_chat(f"[{sender}] {text}")
        except queue.Empty:
            pass
        self.root.after(50, self._poll_inbox)

    # ---------------- Network ----------------
    def connect(self):
        if self.connected:
            return

        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Thiếu tên", "Bạn cần nhập tên trước khi kết nối.")
            return

        ip = self.ip_var.get().strip()
        port_str = self.port_var.get().strip()

        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showerror("Sai Port", "Port phải là số từ 1 đến 65535.")
            return

        self.server_addr = (ip, port)
        self.name = name

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.rudp = ReliableUDP(self.sock)

            # Gửi HELLO để server lưu tên
            self.rudp.send_hello(self.server_addr, self.name)

            # Thread nhận
            def on_message(addr, sender_name, text):
                if text == "__HELLO__":
                    return
                # Đẩy vào queue để UI thread xử lý
                self.inbox.put((sender_name, text))

            self.recv_thread = threading.Thread(target=self.rudp.recv_loop, args=(on_message,), daemon=True)
            self.recv_thread.start()

            self.connected = True
            self._set_status(f"Đã kết nối tới {ip}:{port} (UDP có ACK + resend + giả lập mất gói)")
            self._append_chat(f"[SYSTEM] Bạn đã vào phòng với tên: {self.name}")

            # Khóa phần cấu hình khi đã kết nối
            self.connect_btn.configure(state=tk.DISABLED)
            self.disconnect_btn.configure(state=tk.NORMAL)
            self.send_btn.configure(state=tk.NORMAL)

            self.name_entry.configure(state=tk.DISABLED)
            self.ip_entry.configure(state=tk.DISABLED)
            self.port_entry.configure(state=tk.DISABLED)

            self.msg_entry.focus_set()

        except Exception as e:
            messagebox.showerror("Lỗi kết nối", f"Không thể khởi tạo client.\nChi tiết: {e}")
            self.disconnect()

    def disconnect(self):
        if self.rudp:
            try:
                self.rudp.stop()
            except:
                pass

        if self.sock:
            try:
                self.sock.close()
            except:
                pass

        self.sock = None
        self.rudp = None
        self.recv_thread = None
        self.connected = False

        self._set_status("Chưa kết nối")
        self._append_chat("[SYSTEM] Đã ngắt kết nối.")

        self.connect_btn.configure(state=tk.NORMAL)
        self.disconnect_btn.configure(state=tk.DISABLED)
        self.send_btn.configure(state=tk.DISABLED)

        self.name_entry.configure(state=tk.NORMAL)
        self.ip_entry.configure(state=tk.NORMAL)
        self.port_entry.configure(state=tk.NORMAL)

    def send_message(self):
        if not self.connected or not self.rudp:
            return

        text = self.msg_var.get().strip()
        if not text:
            return

        self.msg_var.set("")

        # Hiển thị tin nhắn của mình ngay (trải nghiệm chat tốt hơn)
        self._append_chat(f"[{self.name}] {text}")

        # Gửi tin bằng reliable UDP (ACK + resend)
        def send_task():
            ok = self.rudp.send_reliable_msg(self.server_addr, text, sender_name=self.name)
            if not ok:
                # Báo lỗi nhẹ (không crash UI)
                self.inbox.put(("SYSTEM", "⚠ Gửi thất bại sau nhiều lần thử (có thể server tắt hoặc mất gói quá nhiều)."))

        threading.Thread(target=send_task, daemon=True).start()

    def on_close(self):
        try:
            self.disconnect()
        finally:
            self.root.destroy()


def main():
    root = tk.Tk()

    # Dùng theme mặc định của ttk cho nhìn gọn gàng
    try:
        style = ttk.Style()
        # Nếu có theme 'clam' thường nhìn ổn
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except:
        pass

    app = ChatClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
