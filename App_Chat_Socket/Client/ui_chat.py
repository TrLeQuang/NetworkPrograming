import tkinter as tk
import re
import os
from tkinter import scrolledtext, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
from protocol import decode_file

class ChatUI:
    def __init__(self, network, username: str):
        self.network = network
        self.username = username

        # state
        self.dm_target = None
        self.selected_room = None
        self.joined_rooms = set()
        self.hist = {}  # Lưu text history
        self._placeholder_text = "Nhập tin nhắn..."
        
        # File attachment
        self.attached_file = None

        # GUI
        self.root = tk.Tk()
        self.root.title(f"Chat App - {username}")
        self.root.geometry("1050x600")
        self.root.minsize(900, 500)

        main = tk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True)

        # LEFT PANEL
        left = tk.Frame(main, width=280, bg="#2f3136")
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

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
        self.chat_area.tag_config("file_link", foreground="#00aff4", underline=True)

        # INPUT AREA
        bottom = tk.Frame(right, bg="#2f3136")
        bottom.pack(fill=tk.X, padx=10, pady=(0, 10))

        # File attachment label
        self.file_label = tk.Label(bottom, text="", bg="#2f3136", fg="#f9e2af",
                                   font=("Segoe UI", 9))
        self.file_label.pack(fill=tk.X, pady=(0, 5))

        input_row = tk.Frame(bottom, bg="#2f3136")
        input_row.pack(fill=tk.X)

        # Attach button
        tk.Button(
            input_row,
            text="📎",
            width=3,
            command=self.attach_file,
            bg="#40444b",
            fg="white",
            relief=tk.FLAT,
            font=("Segoe UI", 12),
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.entry_border = tk.Frame(input_row, bg="#40444b", padx=2, pady=2)
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
            input_row,
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

    # ===== File handling =====
    def attach_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file để gửi",
            filetypes=[
                ("Ảnh", "*.png;*.jpg;*.jpeg;*.gif;*.bmp"),
                ("Tất cả files", "*.*")
            ]
        )
        if file_path:
            file_size = os.path.getsize(file_path)
            if file_size > 5 * 1024 * 1024:
                messagebox.showerror("Lỗi", "File quá lớn (max 5MB)")
                return
            
            self.attached_file = file_path
            file_name = os.path.basename(file_path)
            self.file_label.config(text=f"📎 {file_name} - Click để hủy")
            self.file_label.bind("<Button-1>", lambda e: self.clear_attachment())

    def clear_attachment(self):
        self.attached_file = None
        self.file_label.config(text="")
        self.file_label.unbind("<Button-1>")

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

    def _display_file_live(self, file_data: dict, sender: str, timestamp: str, tag: str):
        """Hiển thị file TRỰC TIẾP trong chat area - KHÔNG tự động lưu"""
        file_name = file_data.get("name", "unknown")
        file_type = file_data.get("type", "")
        file_size = file_data.get("size", 0)
        
        size_kb = file_size / 1024
        size_text = f"{size_kb:.1f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"
        
        self.chat_area.config(state="normal")
        
        # Hiển thị thông tin file
        info_text = f"  [{timestamp}] {sender} đã gửi: {file_name} ({size_text})  \n"
        self.chat_area.insert(tk.END, info_text, tag)
        
        if file_type.startswith("image/"):
            # Hiển thị preview ảnh (không lưu file)
            try:
                from protocol import get_file_preview_data
                from io import BytesIO
                
                img_bytes = get_file_preview_data(file_data)
                if img_bytes:
                    img = Image.open(BytesIO(img_bytes))
                    img.thumbnail((250, 250))
                    photo = ImageTk.PhotoImage(img)
                    
                    label = tk.Label(self.chat_area, image=photo, bg="#36393f", cursor="hand2")
                    label.image = photo  # Keep reference
                    # Click để lưu ảnh
                    label.bind("<Button-1>", lambda e, fd=file_data: self._save_file_on_click(fd))
                    
                    self.chat_area.window_create(tk.END, window=label)
                    self.chat_area.insert(tk.END, "\n")
            except Exception as e:
                self.chat_area.insert(tk.END, f"  ⚠️ Không thể hiển thị ảnh: {e}  \n", "system")
        
        # Tạo nút Download
        download_btn = tk.Button(
            self.chat_area,
            text=f"💾 Tải xuống {file_name}",
            command=lambda fd=file_data: self._save_file_on_click(fd),
            bg="#5865f2",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            font=("Segoe UI", 9)
        )
        self.chat_area.window_create(tk.END, window=download_btn)
        self.chat_area.insert(tk.END, "\n")
        
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def _save_file_on_click(self, file_data: dict):
        """Lưu file khi user click"""
        from protocol import decode_file
        
        saved_path = decode_file(file_data)
        if saved_path:
            messagebox.showinfo("Thành công", f"Đã lưu file:\n{saved_path}")
            # Mở file sau khi lưu (tùy chọn)
            try:
                os.startfile(saved_path)
            except:
                pass
        else:
            messagebox.showerror("Lỗi", "Không thể lưu file")

    # ===== UI events =====
    def on_select_user(self, event=None):
        sel = self.user_list.curselection()
        if not sel:
            return
        u = self.user_list.get(sel[0])
        if u == self.username:
            return

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

        self.dm_target = None
        self.dm_label.config(text="Đang chat với: (chưa chọn)")

        self.selected_room = room
        joined = "Đã join" if room in self.joined_rooms else "Chưa join"
        self.room_label.config(text=f"Phòng đang chọn: {room} ({joined})")
        self.header.config(text=f"CHAT PHÒNG: {room} ({joined})")
        self._render_hist(self._key_room(room))

    def send_message(self, event=None):
        msg = self.entry.get().strip()
        
        if (not msg or msg == self._placeholder_text) and not self.attached_file:
            return

        if msg == self._placeholder_text:
            msg = ""

        # Gửi theo context
        if self.selected_room:
            if self.selected_room not in self.joined_rooms:
                messagebox.showwarning("Chưa join", "Bạn phải Join phòng trước khi gửi tin nhắn.")
                return
            success = self.network.send_group(self.username, self.selected_room, msg, self.attached_file)
            if not success:
                messagebox.showerror("Lỗi", "Không thể gửi tin nhắn. Kiểm tra kết nối.")
                return
            self.entry.delete(0, tk.END)
            self.clear_attachment()
            return

        if self.dm_target:
            success = self.network.send_private(self.username, self.dm_target, msg, self.attached_file)
            if not success:
                messagebox.showerror("Lỗi", "Không thể gửi tin nhắn. Kiểm tra kết nối.")
                return
            self.entry.delete(0, tk.END)
            self.clear_attachment()
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

            m = re.search(r"phòng\s+'([^']+)'", msg)
            room = data.get("room") or (m.group(1) if m else None)

            if room:
                key = self._key_room(room)
                self._append_hist(key, text, "system")
                if self.selected_room == room:
                    self._append_chat_live(text, "system")
                return

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
            file_data = data.get("file")

            other = sender if sender != self.username else to_user
            if not other:
                return

            key = self._key_dm(other)
            tag = "self" if sender == self.username else "other"
            
            # Hiển thị file nếu có VÀ đang ở conversation này
            if file_data and self.dm_target == other:
                self._display_file_live(file_data, sender, ts, tag)
            
            # Lưu vào history (text only)
            if file_data:
                self._append_hist(key, f"  [{ts}] {sender}: [📎 {file_data.get('name')}]  ", tag)
            
            # Hiển thị text message
            if msg:
                text = f"  [{ts}] {sender}: {msg}  "
                self._append_hist(key, text, tag)
                if self.dm_target == other:
                    self._append_chat_live(text, tag)
            return

        if t == "group":
            room = data.get("room")
            sender = data.get("from")
            msg = data.get("msg", "")
            ts = data.get("timestamp", "")
            file_data = data.get("file")

            if not room:
                return

            key = self._key_room(room)
            tag = "self" if sender == self.username else "other"
            
            # Hiển thị file nếu có VÀ đang ở room này
            if file_data and self.selected_room == room:
                self._display_file_live(file_data, sender, ts, tag)
            
            # Lưu vào history (text only)
            if file_data:
                self._append_hist(key, f"  [{ts}] ({room}) {sender}: [📎 {file_data.get('name')}]  ", tag)
            
            # Hiển thị text message
            if msg:
                text = f"  [{ts}] ({room}) {sender}: {msg}  "
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