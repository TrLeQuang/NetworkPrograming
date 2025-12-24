import socket
import threading
from typing import Dict, Tuple

from Config import SERVER_IP, SERVER_PORT, BUFFER_SIZE
from Reliable_UDP import ReliableUDP

# Lưu danh sách user theo địa chỉ
clients: Dict[Tuple[str, int], str] = {}


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))

    rudp = ReliableUDP(sock)

    print(f"🚀 UDP Chat Server chạy tại {SERVER_IP}:{SERVER_PORT}")

    def on_message(addr, name, text):
        global clients

        if text == "__HELLO__":
            clients[addr] = name
            print(f"👋 {name} đã vào phòng: {addr}")
            # Thông báo cho mọi người
            broadcast(f"⚡ {name} đã tham gia phòng chat!", from_name="SERVER", exclude=addr)
            return

        # Nếu chưa HELLO mà gửi MSG thì vẫn cho qua, gán tên tạm
        if addr not in clients:
            clients[addr] = name if name else f"User{addr[1]}"

        sender = clients[addr]
        print(f"[{sender}] {text}")

        # Broadcast cho mọi người (trừ người gửi)
        broadcast(text, from_name=sender, exclude=addr)

    def broadcast(text: str, from_name: str = "SERVER", exclude=None):
        for caddr in list(clients.keys()):
            if exclude is not None and caddr == exclude:
                continue
            ok = rudp.send_reliable_msg(caddr, text, sender_name=from_name)
            if not ok:
                # Nếu gửi fail nhiều lần, coi như client rớt mạng -> remove
                cname = clients.get(caddr, str(caddr))
                print(f"⚠ Không gửi được tới {cname}, loại khỏi phòng.")
                clients.pop(caddr, None)

    # Thread nhận
    t = threading.Thread(target=rudp.recv_loop, args=(on_message,), daemon=True)
    t.start()

    # Server cũng có thể gõ để gửi thông báo
    try:
        while True:
            msg = input()
            if msg.strip().lower() in ["exit", "quit"]:
                break
            broadcast(msg, from_name="SERVER")
    finally:
        rudp.stop()
        sock.close()


if __name__ == "__main__":
    main()

