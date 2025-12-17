#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <thread>
#include <atomic>
#include <string>

#pragma comment(lib, "ws2_32.lib")

static void ApplyTcpOpts(SOCKET s) {
    // Low-latency: disable Nagle
    BOOL noDelay = TRUE;
    setsockopt(s, IPPROTO_TCP, TCP_NODELAY, (char*)&noDelay, sizeof(noDelay));

    // Bigger buffers (optional)
    int buf = 1 << 20;
    setsockopt(s, SOL_SOCKET, SO_SNDBUF, (char*)&buf, sizeof(buf));
    setsockopt(s, SOL_SOCKET, SO_RCVBUF, (char*)&buf, sizeof(buf));
}

int main() {
    WSADATA wsa{};
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 1;

    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) return 1;

    ApplyTcpOpts(sock);

    sockaddr_in server{};
    server.sin_family = AF_INET;
    server.sin_port = htons(9000);
    server.sin_addr.s_addr = inet_addr("127.0.0.1");

    if (connect(sock, (sockaddr*)&server, sizeof(server)) != 0) {
        std::cerr << "[CLIENT] connect failed: " << WSAGetLastError() << "\n";
        closesocket(sock);
        WSACleanup();
        return 1;
    }

    std::cout << "[CLIENT] Connected!\n";
    std::cout << "Type messages. Type 'exit' to quit.\n\n";

    std::atomic<bool> running(true);

    std::thread recvThread([&]() {
        char buf[2048];
        while (running) {
            int n = recv(sock, buf, (int)sizeof(buf) - 1, 0);
            if (n <= 0) { running = false; break; }
            buf[n] = '\0';
            std::cout << "\n[SERVER] " << buf << "\n[CLIENT] > " << std::flush;
        }
        });

    std::thread sendThread([&]() {
        std::string line;
        std::cout << "[CLIENT] > " << std::flush;
        while (running && std::getline(std::cin, line)) {
            if (line == "exit") {
                running = false;
                shutdown(sock, SD_BOTH);
                break;
            }
            line += "\n";
            send(sock, line.c_str(), (int)line.size(), 0);
            std::cout << "[CLIENT] > " << std::flush;
        }
        });

    sendThread.join();
    recvThread.join();

    closesocket(sock);
    WSACleanup();
    return 0;
}
