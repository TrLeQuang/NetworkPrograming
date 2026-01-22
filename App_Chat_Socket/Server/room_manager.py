import threading
from typing import Dict, Set, List


class RoomManager:
    """
    Quản lý phòng chat:
    - room tồn tại ngay khi create (kể cả chưa ai join)
    - join/leave theo username
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._rooms: Dict[str, Set[str]] = {}

    def create_room(self, room: str) -> bool:
        room = (room or "").strip()
        if not room:
            return False
        with self._lock:
            if room in self._rooms:
                return False
            self._rooms[room] = set()
            return True

    def room_exists(self, room: str) -> bool:
        room = (room or "").strip()
        with self._lock:
            return room in self._rooms

    def join(self, room: str, user: str) -> bool:
        room = (room or "").strip()
        user = (user or "").strip()
        if not room or not user:
            return False
        with self._lock:
            if room not in self._rooms:
                return False
            self._rooms[room].add(user)
            return True

    def leave(self, room: str, user: str) -> bool:
        room = (room or "").strip()
        user = (user or "").strip()
        if not room or not user:
            return False
        with self._lock:
            if room not in self._rooms:
                return False
            self._rooms[room].discard(user)
            return True

    def members(self, room: str) -> List[str]:
        room = (room or "").strip()
        with self._lock:
            return sorted(list(self._rooms.get(room, set())))

    def remove_user_everywhere(self, user: str) -> None:
        user = (user or "").strip()
        if not user:
            return
        with self._lock:
            for members in self._rooms.values():
                members.discard(user)

    def snapshot(self) -> list[dict]:
        """
        Trả về:
        [{"name":"room1","members":["A","B"]}, ...]
        """
        with self._lock:
            out = []
            for name, members in self._rooms.items():
                out.append({"name": name, "members": sorted(list(members))})
            out.sort(key=lambda x: x["name"].lower())
            return out

