from typing import Dict, Optional, Any


class UserManager:
    """
    Quản lý danh sách user online trên server.
    Map: username -> handler (ClientHandler).
    """

    def __init__(self):
        # dict lưu: username -> handler (đối tượng ClientHandler)
        self._users: Dict[str, Any] = {}

    def add_user(self, username: str, handler: Any) -> bool:
        """
        Thêm user mới.
        Trả về False nếu username đã tồn tại (không thêm).
        """
        if username in self._users:
            return False
        self._users[username] = handler
        return True

    def remove_user(self, username: str) -> None:
        """
        Xóa user khỏi danh sách online (nếu tồn tại).
        """
        if username in self._users:
            del self._users[username]

    def get_handler(self, username: str) -> Optional[Any]:
        """
        Lấy handler (ClientHandler) theo username, nếu có.
        Dùng cho chat riêng (private) nếu sau này cần.
        """
        return self._users.get(username)

    def get_online_users(self) -> list[str]:
        """
        Trả về danh sách username online.
        """
        return list(self._users.keys())

    def has_user(self, username: str) -> bool:
        """
        Kiểm tra username đã tồn tại hay chưa.
        """
        return username in self._users