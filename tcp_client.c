#include <stdio.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")

int main() {
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);

    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    
    struct sockaddr_in server = { 0 };
    server.sin_family = AF_INET;
    server.sin_port = htons(8080);
    inet_pton(AF_INET, "127.0.0.1", &server.sin_addr);

    if (connect(sock, (SOCKADDR*)&server, sizeof(server)) == SOCKET_ERROR) {
        printf("Loi: Khong the ket noi den Server! (Hay chay Server truoc)\n");
        return 1;
    }

    printf("Da ket noi thanh cong! Nhap tin nhan (go 'exit' de thoat):\n");

    char msg[1024];
    char buf[1024];

    while (1) {
        printf("Client > ");
        fgets(msg, sizeof(msg), stdin);
        msg[strcspn(msg, "\n")] = 0; // Xoa ky tu xuong dong tu fgets

        if (strcmp(msg, "exit") == 0) break;

        send(sock, msg, (int)strlen(msg), 0);

        // Doi nhan phan hoi tu Server
        int bytes = recv(sock, buf, sizeof(buf) - 1, 0);
        if (bytes > 0) {
            buf[bytes] = '\0';
            printf("[PHAN HOI]: %s\n", buf);
        }
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}