import tkinter as tk
import re
from tkinter import scrolledtext, messagebox, simpledialog


class ChatUI:
    def __init__(self, network, username: str):
        self.network = network
        self.username = username

        # state
        self.dm_target = None            # user đang chọn để chat riêng
        self.selected_room = None        # room đang chọn ở danh sách
        self.joined_rooms = set()        # room mà user đã join (từ room_list server)

        # lịch sử theo hội thoại
        self.hist = {}  # key -> list[(text, tag)], key = "DM:<u>" hoặc "ROOM:<r>"

        # placeholder
        self._placeholder_text = "Nhập tin nhắn..."

        # GUI
        self.root = tk.Tk()
        self.root.title(f"Chat App - {username}")
        self.root.geometry("1050x560")
        self.root.minsize(900, 500)

        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)

        # LEFT PANEL
        left = tk.Frame(main, width=280, bg="#2f3136")
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        # ===== Private area =====
        tk.Label(left, text="CHAT RIÊNG (1-1)", bg="#2f3136", fg="white",
                 font=("Segoe UI", 11, "bold")).pack(pady=(12, 6))

        self.user_list = tk.Listbox(left, bg="#2f3136", fg="white",
                                    relief=tk.FLAT, selectbackground="#40444b",
                                    highlightthickness=0, height=10)
        self.user_list.pack(fill=tk.X, padx=10)
        self.user_list.bind("<<ListboxSelect>>", self.on_select_user)

        self.dm_label = tk.Label(left, text="Đang chat với: (chưa chọn)", bg="#2f3136",
                                 fg="#b9bbbe", font=("Segoe UI", 10))
        self.dm_label.pack(pady=(6, 10))

        # ===== Room area =====
        tk.Label(left, text="CHAT PHÒNG", bg="#2f3136", fg="white",
                 font=("Segoe UI", 11, "bold")).pack(pady=(4, 6))

        self.room_list = tk.Listbox(left, bg="#2f3136", fg="white",
                                    relief=tk.FLAT, selectbackground="#40444b",
                                    highlightthickness=0, height=10)
        self.room_list.pack(fill=tk.BOTH, expand=True, padx=10)
        self.room_list.bind("<<ListboxSelect>>", self.on_select_room)

        btns = tk.Frame(left, bg="#2f3136")
        btns.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btns, text="Tạo phòng", command=self.create_room,
                  bg="#5865f2", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))
        tk.Button(btns, text="Join", command=self.join_room,
                  bg="#3ba55c", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 4))
        tk.Button(btns, text="Leave", command=self.leave_room,
                  bg="#ed4245", fg="white", relief=tk.FLAT).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

        self.room_label = tk.Label(left, text="Phòng đang chọn: (chưa chọn)", bg="#2f3136",
                                   fg="#b9bbbe", font=("Segoe UI", 10))
        self.room_label.pack(pady=(0, 8))

        # RIGHT PANEL
        right = tk.Frame(main, bg="#36393f")
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.header = tk.Label(right, text="Chọn user để chat riêng hoặc chọn phòng để xem",
                               bg="#36393f", fg="white",
                               font=("Segoe UI", 11, "bold"), anchor="w")
        self.header.pack(fill=tk.X, padx=10, pady=(10, 6))

        self.chat_area = scrolledtext.ScrolledText(right, state="disabled", wrap=tk.WORD,
                                                   bg="#36393f", fg="white",
                                                   insertbackground="white", relief=tk.FLAT)
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        self.chat_area.tag_config("self", justify="right", background="#5865f2", foreground="white",
                                  lmargin1=240, lmargin2=240, rmargin=15, spacing1=4, spacing3=4)
        self.chat_area.tag_config("other", justify="left", background="#40444b", foreground="white",
                                  lmargin1=15, lmargin2=15, rmargin=240, spacing1=4, spacing3=4)
        self.chat_area.tag_config("system", justify="center", foreground="#b9bbbe", spacing1=6, spacing3=6)

        # =========================
        # INPUT AREA
        # =========================
        bottom = tk.Frame(right, bg="#2f3136")
        bottom.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.entry_border = tk.Frame(bottom, bg="#40444b", padx=2, pady=2)
        self.entry_border.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.entry = tk.Entry(
            self.entry_border,
            bg="#111827",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT,
            font=("Segoe UI", 11),
        )
        self.entry.pack(fill=tk.X, padx=10, pady=8)

        # placeholder
        self.entry.insert(0, self._placeholder_text)
        self.entry.config(fg="#9ca3af")

        def _on_focus_in(e):
            if self.entry.get() == self._placeholder_text:
                self.entry.delete(0, tk.END)
                self.entry.config(fg="white")
            self.entry_border.config(bg="#5865f2")

        def _on_focus_out(e):
            if not self.entry.get().strip():
                self.entry.delete(0, tk.END)
                self.entry.insert(0, self._placeholder_text)
                self.entry.config(fg="#9ca3af")
            self.entry_border.config(bg="#40444b")

        self.entry.bind("<FocusIn>", _on_focus_in)
        self.entry.bind("<FocusOut>", _on_focus_out)
        self.entry.bind("<Return>", self.send_message)

        tk.Button(
            bottom,
            text="Send",
            width=10,
            command=self.send_message,
            bg="#5865f2",
            fg="white",
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        ).pack(side=tk.RIGHT)

        # network
        self.network.set_on_message(self.on_message)
        self.network.set_on_disconnect(self.on_disconnect)
        self.network.send_login(self.username)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    # ===== helpers =====
    def _key_dm(self, other: str) -> str:
        return f"DM:{other}"

    def _key_room(self, room: str) -> str:
        return f"ROOM:{room}"

    def _append_hist(self, key: str, text: str, tag: str):
        self.hist.setdefault(key, []).append((text, tag))

    def _render_hist(self, key: str | None):
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", tk.END)
        if key and key in self.hist:
            for text, tag in self.hist[key]:
                self.chat_area.insert(tk.END, text + "\n", tag)
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def _append_chat_live(self, text: str, tag: str):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, text + "\n", tag)
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    # ===== UI events =====
    def on_select_user(self, event=None):
        sel = self.user_list.curselection()
        if not sel:
            return
        u = self.user_list.get(sel[0])
        if u == self.username:
            return

        # ✅ CHỌN USER => TẮT CHAT PHÒNG
        self.selected_room = None
        self.room_label.config(text="Phòng đang chọn: (chưa chọn)")
        self.header.config(text=f"CHAT RIÊNG với: {u}")

        self.dm_target = u
        self.dm_label.config(text=f"Đang chat với: {u}")
        self._render_hist(self._key_dm(u))

    def on_select_room(self, event=None):
        sel = self.room_list.curselection()
        if not sel:
            return
        room = self.room_list.get(sel[0]).split(" (", 1)[0].strip()

        # ✅ CHỌN ROOM => TẮT CHAT RIÊNG
        self.dm_target = None
        self.dm_label.config(text="Đang chat với: (chưa chọn)")

        self.selected_room = room
        joined = "Đã join" if room in self.joined_rooms else "Chưa join"
        self.room_label.config(text=f"Phòng đang chọn: {room} ({joined})")
        self.header.config(text=f"CHAT PHÒNG: {room} ({joined})")
        self._render_hist(self._key_room(room))

    def send_message(self, event=None):
        msg = self.entry.get().strip()

        if (not msg) or (msg == self._placeholder_text):
            return

        # ✅ ƯU TIÊN THEO CONTEXT:
        # Nếu đang chọn room => gửi group (không bị dm_target cũ phá nữa)
        if self.selected_room:
            if self.selected_room not in self.joined_rooms:
                messagebox.showwarning("Chưa join", "Bạn phải Join phòng trước khi gửi tin nhắn.")
                return
            self.network.send_group(self.username, self.selected_room, msg)
            self.entry.delete(0, tk.END)
            return

        # Nếu không chọn room thì mới chat riêng
        if self.dm_target:
            self.network.send_private(self.username, self.dm_target, msg)
            self.entry.delete(0, tk.END)
            return

        messagebox.showinfo("Chưa chọn", "Hãy chọn user để chat riêng hoặc chọn phòng để chat nhóm.")

    def create_room(self):
        room = simpledialog.askstring("Tạo phòng", "Nhập tên phòng:")
        if not room:
            return
        self.network.create_room(self.username, room.strip())

    def join_room(self):
        if not self.selected_room:
            messagebox.showinfo("Join", "Hãy chọn 1 phòng trong danh sách.")
            return
        self.network.join_room(self.username, self.selected_room)

    def leave_room(self):
        if not self.selected_room:
            messagebox.showinfo("Leave", "Hãy chọn 1 phòng trong danh sách.")
            return
        self.network.leave_room(self.username, self.selected_room)

    # ===== network callbacks =====
    def on_message(self, data: dict):
        t = data.get("type")

        if t == "user_list":
            users = data.get("users", [])
            self.user_list.delete(0, tk.END)
            for u in users:
                self.user_list.insert(tk.END, u)
            if self.dm_target and self.dm_target not in users:
                self.dm_target = None
                self.dm_label.config(text="Đang chat với: (chưa chọn)")
            return

        if t == "room_list":
            rooms = data.get("rooms", [])
            new_joined = set()
            self.room_list.delete(0, tk.END)
            for r in rooms:
                name = r.get("name", "")
                members = r.get("members", [])
                if self.username in members:
                    new_joined.add(name)
                self.room_list.insert(tk.END, f"{name} ({len(members)})")
            self.joined_rooms = new_joined

            if self.selected_room:
                joined = "Đã join" if self.selected_room in self.joined_rooms else "Chưa join"
                self.room_label.config(text=f"Phòng đang chọn: {self.selected_room} ({joined})")
                self.header.config(text=f"CHAT PHÒNG: {self.selected_room} ({joined})")
            return

        if t == "system":
            msg = data.get("msg", "")
            text = f"🔔 {msg}"

            # Server chưa gửi room => UI tự parse từ msg: "... phòng 'G1'"
            m = re.search(r"phòng\s+'([^']+)'", msg)
            room = data.get("room") or (m.group(1) if m else None)

            if room:
                key = self._key_room(room)
                self._append_hist(key, text, "system")
                if self.selected_room == room:
                    self._append_chat_live(text, "system")
                return

            # system chung
            self._append_hist("SYSTEM", text, "system")
            self._append_chat_live(text, "system")
            return

        if t == "error":
            self._append_chat_live(f"❌ {data.get('msg','')}", "system")
            return

        if t == "private":
            sender = data.get("from")
            to_user = data.get("to")
            msg = data.get("msg", "")
            ts = data.get("timestamp", "")

            other = sender if sender != self.username else to_user
            if not other:
                return

            key = self._key_dm(other)
            text = f"  [{ts}] {sender}: {msg}  "
            tag = "self" if sender == self.username else "other"
            self._append_hist(key, text, tag)

            if self.dm_target == other:
                self._append_chat_live(text, tag)
            return

        if t == "group":
            room = data.get("room")
            sender = data.get("from")
            msg = data.get("msg", "")
            ts = data.get("timestamp", "")

            if not room:
                return

            key = self._key_room(room)
            text = f"  [{ts}] ({room}) {sender}: {msg}  "
            tag = "self" if sender == self.username else "other"
            self._append_hist(key, text, tag)

            if self.selected_room == room:
                self._append_chat_live(text, tag)
            return

    def on_disconnect(self):
        self._append_chat_live("⚠️ Mất kết nối server", "system")

    def on_close(self):
        try:
            self.network.send_logout(self.username)
            self.network.disconnect()
        except Exception:
            pass
        self.root.destroy()
