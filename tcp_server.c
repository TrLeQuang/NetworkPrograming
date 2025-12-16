#include <stdio.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

int main() {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);

    SOCKET server = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    int opt = 1;
    setsockopt(server, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt));

    struct sockaddr_in addr = { 0 };
    addr.sin_family = AF_INET;
    addr.sin_port = htons(8080);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(server, (SOCKADDR*)&addr, sizeof(addr));
    listen(server, 5);

    printf("--- SERVER DANG CHO KET NOI (CONG 8080) ---\n");
    SOCKET client = accept(server, NULL, NULL);
    printf("Co Client da ket noi!\n");

    char buf[1024];
    while (1) {
        int bytes_received = recv(client, buf, sizeof(buf) - 1, 0);
        if (bytes_received <= 0) {
            printf("Client da ngat ket noi.\n");
            break;
        }

        buf[bytes_received] = '\0'; // Them ky tu ket thuc chuoi de in dung
        printf("Client gui: %s\n", buf);

        // Gui lai xac nhan (Echo)
        char response[1100];
        sprintf(response, "Server da nhan: %s", buf);
        send(client, response, (int)strlen(response), 0);
    }

    closesocket(client);
    closesocket(server);
    WSACleanup();
    return 0;
}