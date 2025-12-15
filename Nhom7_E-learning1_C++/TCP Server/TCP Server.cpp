#define _WINSOCK_DEPRECATED_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>

#pragma comment(lib, "ws2_32.lib")

int main() {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);

    SOCKET server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(9000);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(server, (sockaddr*)&addr, sizeof(addr));
    listen(server, 5);

    std::cout << "[SERVER] Listening on port 9000...\n";

    SOCKET client = accept(server, nullptr, nullptr);
    std::cout << "[SERVER] Client connected!\n";

    char buffer[1024];
    int bytes = recv(client, buffer, sizeof(buffer) - 1, 0);
    if (bytes > 0) {
        buffer[bytes] = '\0';
        std::cout << "[CLIENT]: " << buffer;

        const char* reply = "Hello from TCP Server\n";
        send(client, reply, strlen(reply), 0);
    }

    closesocket(client);
    closesocket(server);
    WSACleanup();
    return 0;
}
