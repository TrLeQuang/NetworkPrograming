import random
import socket
import threading
import time
from typing import Dict, Tuple, Optional, Set

from Config import ACK_TIMEOUT, MAX_RETRY, LOSS_RATE
from Protocol import Packet


class ReliableUDP:
    """
    Lớp này gói UDP thường thành "gần giống tin cậy":
    - Gói MSG có seq
    - Bên nhận gửi ACK(seq)
    - Bên gửi nếu chưa thấy ACK thì resend
    - Bên nhận chống trùng (deduplicate)
    """

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.sock_lock = threading.Lock()

        # Quản lý seq gửi đi theo từng peer (addr)
        self.send_seq: Dict[Tuple[str, int], int] = {}

        # Các ACK đã nhận (theo addr -> set(seq))
        self.acked: Dict[Tuple[str, int], Set[int]] = {}
        self.acked_lock = threading.Lock()

        # Chống nhận trùng (theo addr -> set(seq đã xử lý))
        self.received_seen: Dict[Tuple[str, int], Set[int]] = {}
        self.recv_lock = threading.Lock()

        self.running = True

    def stop(self):
        self.running = False

    def _maybe_drop(self) -> bool:
        """Giả lập mất gói (để thấy resend hoạt động)."""
        return random.random() < LOSS_RATE

    def _next_seq(self, addr: Tuple[str, int]) -> int:
        cur = self.send_seq.get(addr, 0)
        self.send_seq[addr] = cur + 1
        return cur

    def mark_acked(self, addr: Tuple[str, int], seq: int):
        with self.acked_lock:
            if addr not in self.acked:
                self.acked[addr] = set()
            self.acked[addr].add(seq)

    def is_acked(self, addr: Tuple[str, int], seq: int) -> bool:
        with self.acked_lock:
            return seq in self.acked.get(addr, set())

    def already_seen(self, addr: Tuple[str, int], seq: int) -> bool:
        with self.recv_lock:
            return seq in self.received_seen.get(addr, set())

    def mark_seen(self, addr: Tuple[str, int], seq: int):
        with self.recv_lock:
            if addr not in self.received_seen:
                self.received_seen[addr] = set()
            self.received_seen[addr].add(seq)

    def send_reliable_msg(self, addr: Tuple[str, int], text: str, sender_name: str = "") -> bool:
        """
        Gửi MSG tin cậy. Return True nếu nhận ACK thành công, False nếu fail.
        """
        seq = self._next_seq(addr)
        pkt = Packet(type="MSG", seq=seq, name=sender_name, text=text)

        for attempt in range(1, MAX_RETRY + 1):
            # Giả lập mất gói phía gửi (drop trước khi send)
            if self._maybe_drop():
                print(f"❌ (Giả lập) DROP gói gửi đi seq={seq} -> {addr} (lần {attempt})")
            else:
                with self.sock_lock:
                    self.sock.sendto(pkt.to_bytes(), addr)

            # Chờ ACK
            start = time.time()
            while time.time() - start < ACK_TIMEOUT:
                if self.is_acked(addr, seq):
                    return True
                time.sleep(0.02)

            print(f"⏱ Timeout ACK seq={seq} -> resend (lần {attempt})")

        return False

    def send_ack(self, addr: Tuple[str, int], seq: int):
        ack_pkt = Packet(type="ACK", ack=seq)
        # Giả lập mất gói ACK
        if self._maybe_drop():
            print(f"❌ (Giả lập) DROP ACK seq={seq} -> {addr}")
            return
        with self.sock_lock:
            self.sock.sendto(ack_pkt.to_bytes(), addr)

    def send_hello(self, addr: Tuple[str, int], name: str):
        # HELLO không cần reliable quá chặt, gửi vài lần cho chắc
        pkt = Packet(type="HELLO", name=name)
        for _ in range(2):
            if not self._maybe_drop():
                with self.sock_lock:
                    self.sock.sendto(pkt.to_bytes(), addr)
            time.sleep(0.05)

    def recv_loop(self, on_message):
        """
        Loop nhận:
        - Nếu ACK: mark acked
        - Nếu MSG: gửi ACK + chống trùng + callback on_message(addr, name, text)
        - Nếu HELLO: callback on_message(addr, name, "__HELLO__")
        """
        self.sock.settimeout(0.3)

        while self.running:
            try:
                raw, addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                pkt = Packet.from_bytes(raw)
            except Exception:
                continue

            if pkt.type == "ACK":
                self.mark_acked(addr, pkt.ack)

            elif pkt.type == "HELLO":
                on_message(addr, pkt.name, "__HELLO__")

            elif pkt.type == "MSG":
                # Gửi ACK trước
                self.send_ack(addr, pkt.seq)

                # Chống trùng
                if self.already_seen(addr, pkt.seq):
                    continue
                self.mark_seen(addr, pkt.seq)

                on_message(addr, pkt.name, pkt.text)

