import os
from datetime import datetime

class ChatLogger:
    """
    Ghi log server ra file để làm minh chứng thực nghiệm.
    Mỗi ngày 1 file: logs/chat_YYYYMMDD.txt
    """
    def __init__(self, folder: str = "logs"):
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)
        self.file_path = self._build_path()

    def _build_path(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.folder, f"chat_{date_str}.txt")

    def write(self, level: str, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {message}\n"
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(line)