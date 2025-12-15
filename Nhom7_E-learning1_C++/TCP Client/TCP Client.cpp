#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <mstcpip.h>
#include <iostream>

#pragma comment(lib, "ws2_32.lib")

int main() {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);

    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    // ===== TCP OPTIMIZATION =====
    BOOL noDelay = TRUE;
    setsockopt(sock, IPPROTO_TCP, TCP_NODELAY,
        (char*)&noDelay, sizeof(noDelay));

    int bufSize = 1 << 20; // 1MB
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF,
        (char*)&bufSize, sizeof(bufSize));
    setsockopt(sock, SOL_SOCKET, SO_RCVBUF,
        (char*)&bufSize, sizeof(bufSize));

    int timeout = 3000;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO,
        (char*)&timeout, sizeof(timeout));
    // ============================

    sockaddr_in server{};
    server.sin_family = AF_INET;
    server.sin_port = htons(9000);
    server.sin_addr.s_addr = inet_addr("127.0.0.1");

    connect(sock, (sockaddr*)&server, sizeof(server));
    std::cout << "[CLIENT] Connected to server\n";

    const char* msg = "Hello TCP Server (C++ optimized)\n";
    send(sock, msg, strlen(msg), 0);

    char buffer[1024];
    int bytes = recv(sock, buffer, sizeof(buffer) - 1, 0);
    if (bytes > 0) {
        buffer[bytes] = '\0';
        std::cout << "[SERVER]: " << buffer;
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}
