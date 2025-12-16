import socket

HOST = "127.0.0.1"
PORT = 8888

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

try:
    client.connect((HOST, PORT))
    print("[CLIENT] Connected to server")
    print("Type message (type 'exit' to quit):")

    while True:
        msg = input("> ")
        if msg.lower() == "exit":
            break

        client.sendall(msg.encode())

        data = client.recv(1024)
        if not data:
            print("[CLIENT] Server closed connection")
            break

        print("[CLIENT] Server reply:", data.decode())

except ConnectionRefusedError:
    print("[ERROR] Cannot connect to server")
except Exception as e:
    print("[ERROR]", e)
finally:
    client.close()
    print("[CLIENT] Disconnected")
