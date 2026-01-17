import threading
import random
import time
from client_network import ClientNetwork


def run_bot(name: str, duration_sec: int = 10):
    net = ClientNetwork()
    if not net.connect():
        return

    net.send_login(name)

    start = time.time()
    i = 0
    while time.time() - start < duration_sec:
        i += 1
        net.send_message(name, f"bot-msg-{i} from {name}")
        time.sleep(random.uniform(0.2, 0.8))

    net.send_logout(name)
    net.disconnect()


def stress_test(num_clients: int = 10, duration_sec: int = 10):
    threads = []
    for i in range(num_clients):
        name = f"Bot{i+1}"
        t = threading.Thread(target=run_bot, args=(name, duration_sec), daemon=True)
        threads.append(t)
        t.start()
        time.sleep(0.1)

    for t in threads:
        t.join()


if __name__ == "__main__":
    stress_test(num_clients=15, duration_sec=12)

