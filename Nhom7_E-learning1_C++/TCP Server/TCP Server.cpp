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

    SOCKET server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (server == INVALID_SOCKET) return 1;

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(9000);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(server, (sockaddr*)&addr, sizeof(addr));
    listen(server, 5);

    std::cout << "[SERVER] Listening on port 9000...\n";
    SOCKET client = accept(server, nullptr, nullptr);
    if (client == INVALID_SOCKET) {
        closesocket(server);
        WSACleanup();
        return 1;
    }

    ApplyTcpOpts(client);
    std::cout << "[SERVER] Client connected!\n";
    std::cout << "Type messages. Type 'exit' to quit.\n\n";

    std::atomic<bool> running(true);

    std::thread recvThread([&]() {
        char buf[2048];
        while (running) {
            int n = recv(client, buf, (int)sizeof(buf) - 1, 0);
            if (n <= 0) { running = false; break; }
            buf[n] = '\0';
            std::cout << "\n[CLIENT] " << buf << "\n[SERVER] > " << std::flush;
        }
        });

    std::thread sendThread([&]() {
        std::string line;
        std::cout << "[SERVER] > " << std::flush;
        while (running && std::getline(std::cin, line)) {
            if (line == "exit") {
                running = false;
                shutdown(client, SD_BOTH);
                break;
            }
            line += "\n";
            send(client, line.c_str(), (int)line.size(), 0);
            std::cout << "[SERVER] > " << std::flush;
        }
        });

    sendThread.join();
    recvThread.join();

    closesocket(client);
    closesocket(server);
    WSACleanup();
    return 0;
}
