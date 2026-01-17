import tkinter as tk
from tkinter import scrolledtext


class ChatUI:
    def __init__(self, network, username: str):
        self.network = network
        self.username = username

        self.root = tk.Tk()
        self.root.title(f"Chat Room - {username}")
        self.root.geometry("900x500")
        self.root.minsize(800, 450)

        # ================== LAYOUT ==================
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ---------- LEFT: USER LIST ----------
        left_frame = tk.Frame(main_frame, width=200, bg="#2f3136")
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            left_frame,
            text="ONLINE",
            bg="#2f3136",
            fg="white",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=10)

        self.user_list = tk.Listbox(
            left_frame,
            bg="#2f3136",
            fg="white",
            relief=tk.FLAT,
            selectbackground="#40444b",
            highlightthickness=0
        )
        self.user_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=5)

        # ---------- RIGHT: CHAT ----------
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.chat_area = scrolledtext.ScrolledText(
            right_frame,
            state="disabled",
            wrap=tk.WORD,
            bg="#36393f",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ================== CHAT MESSAGE STYLE ==================
        self.chat_area.tag_config(
            "self",
            justify="right",
            background="#5865f2",
            foreground="white",
            lmargin1=180,
            lmargin2=180,
            rmargin=15,
            spacing1=4,
            spacing3=4
        )

        self.chat_area.tag_config(
            "other",
            justify="left",
            background="#40444b",
            foreground="white",
            lmargin1=15,
            lmargin2=15,
            rmargin=180,
            spacing1=4,
            spacing3=4
        )

        self.chat_area.tag_config(
            "system",
            justify="center",
            foreground="#b9bbbe",
            spacing1=6,
            spacing3=6
        )

        # ---------- INPUT ----------
        bottom_frame = tk.Frame(right_frame, bg="#2f3136")
        bottom_frame.pack(fill=tk.X, padx=8, pady=8)

        self.entry_border = tk.Frame(
            bottom_frame,
            bg="#40444b",
            padx=2,
            pady=2
        )
        self.entry_border.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.entry_msg = tk.Entry(
            self.entry_border,
            bg="#36393f",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT,
            font=("Segoe UI", 11)
        )
        self.entry_msg.pack(fill=tk.X, padx=8, pady=6)
        self.entry_msg.bind("<Return>", self.send_message)

        self.entry_msg.bind("<FocusIn>", lambda e: self.entry_border.config(bg="#5865f2"))
        self.entry_msg.bind("<FocusOut>", lambda e: self.entry_border.config(bg="#40444b"))

        tk.Button(
            bottom_frame,
            text="Send",
            width=10,
            command=self.send_message,
            bg="#5865f2",
            fg="white",
            activebackground="#4752c4",
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.RIGHT, padx=8)

        # ================== NETWORK ==================
        self.network.set_on_message(self.on_message)
        self.network.set_on_disconnect(self.on_disconnect)
        self.network.send_login(self.username)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    # ================== EVENT ==================
    def send_message(self, event=None):
        msg = self.entry_msg.get().strip()
        if msg:
            self.network.send_message(self.username, msg)
            self.entry_msg.delete(0, tk.END)

    def on_message(self, data: dict):
        msg_type = data.get("type")

        if msg_type == "message":
            sender = data.get("from")
            timestamp = data.get("timestamp")
            msg = data.get("msg")

            text = f"  [{timestamp}] {sender}: {msg}  "

            if sender == self.username:
                self.append_chat(text, "self")
            else:
                self.append_chat(text, "other")

        elif msg_type == "system":
            text = f"{data.get('msg')}"
            self.append_chat(text, "system")

        elif msg_type == "user_list":
            self.update_user_list(data.get("users", []))

        elif msg_type == "error":
            self.append_chat(data.get("msg"), "system")

    # ================== UI HELPER ==================
    def append_chat(self, text: str, tag: str):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, text + "\n", tag)
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def update_user_list(self, users: list):
        self.user_list.delete(0, tk.END)
        for user in users:
            self.user_list.insert(tk.END, user)

    def on_disconnect(self):
        self.append_chat("⚠️ Mất kết nối server", "system")

    def on_close(self):
        try:
            self.network.send_logout(self.username)
            self.network.disconnect()
        except:
            pass
        self.root.destroy()

