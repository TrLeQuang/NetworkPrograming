from typing import Dict, Optional, Any
import threading


class UserManager:
    """
    Quản lý danh sách user online trên server.
    Map: username -> handler (ClientHandler).
    Thread-safe (vì nhiều ClientHandler thread add/remove).
    """

    def __init__(self):
        self._users: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def add_user(self, username: str, handler: Any) -> bool:
        with self._lock:
            if username in self._users:
                return False
            self._users[username] = handler
            return True

    def remove_user(self, username: str) -> None:
        with self._lock:
            if username in self._users:
                del self._users[username]

    def get_handler(self, username: str) -> Optional[Any]:
        with self._lock:
            return self._users.get(username)

    def get_online_users(self) -> list[str]:
        with self._lock:
            return list(self._users.keys())

    def has_user(self, username: str) -> bool:
        with self._lock:
            return username in self._users
