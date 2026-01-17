# ui_login.py
import tkinter as tk
from tkinter import messagebox
from client_network import ClientNetwork
from ui_chat import ChatUI


class LoginUI:
    def __init__(self):
        self.network = ClientNetwork()

        self.root = tk.Tk()
        self.root.title("Chat App - Login")
        self.root.geometry("320x220")
        self.root.resizable(False, False)
        self.root.configure(bg="#2f3136")

        # ================== TITLE ==================
        tk.Label(
            self.root,
            text="CHAT LOGIN",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#2f3136"
        ).pack(pady=(20, 10))

        # ================== USERNAME INPUT ==================
        self.entry_border = tk.Frame(
            self.root,
            bg="#40444b",
            padx=2,
            pady=2
        )
        self.entry_border.pack(pady=10)

        self.entry_username = tk.Entry(
            self.entry_border,
            font=("Segoe UI", 11),
            bg="#36393f",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT,
            width=22
        )
        self.entry_username.pack(ipady=6)
        self.entry_username.focus()

        # Focus effect
        self.entry_username.bind(
            "<FocusIn>",
            lambda e: self.entry_border.config(bg="#5865f2")
        )
        self.entry_username.bind(
            "<FocusOut>",
            lambda e: self.entry_border.config(bg="#40444b")
        )

        # Enter = Login
        self.entry_username.bind("<Return>", self.login)

        # ================== LOGIN BUTTON ==================
        tk.Button(
            self.root,
            text="Login",
            width=18,
            command=self.login,
            bg="#5865f2",
            fg="white",
            activebackground="#4752c4",
            relief=tk.FLAT,
            font=("Segoe UI", 10, "bold")
        ).pack(pady=15)

        # ================== FOOTER ==================
        tk.Label(
            self.root,
            text="Press Enter to continue",
            font=("Segoe UI", 9),
            fg="#b9bbbe",
            bg="#2f3136"
        ).pack()

    # ================== LOGIN LOGIC ==================
    def login(self, event=None):
        username = self.entry_username.get().strip()
        if not username:
            messagebox.showerror("Error", "Username không được để trống")
            return

        if not self.network.connect():
            messagebox.showerror("Error", "Không thể kết nối server")
            return

        self.root.destroy()
        ChatUI(self.network, username)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    LoginUI().run()

