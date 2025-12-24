import json
from dataclasses import dataclass

# Định nghĩa format gói tin (đơn giản, dễ debug)
# type: "HELLO" | "MSG" | "ACK"
# seq: số thứ tự gói
# name: tên user (HELLO)
# text: nội dung chat (MSG)
# ack: số seq được xác nhận (ACK)

@dataclass
class Packet:
    type: str
    seq: int = 0
    name: str = ""
    text: str = ""
    ack: int = 0

    def to_bytes(self) -> bytes:
        return json.dumps(self.__dict__, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def from_bytes(raw: bytes) -> "Packet":
        data = json.loads(raw.decode("utf-8", errors="ignore"))
        return Packet(**data)

