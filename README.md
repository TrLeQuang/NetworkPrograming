# NetworkPrograming
Đây là tất cả các file bài tập e-learning và đồ án giữa kì và cuối kì của môn lập trình mạng

Bài cuối kỳ ứng dụng chat

Thành viên 1: Phạm Đăng Khoa phụ trách server core
SERVER - host: 127.0.0.1, port:5555
- Code Server giao thức TCP bằng Socket
- Accept nhiều client
- Thread cho mỗi client
- Broadcast message
- Xử lý client disconnect
Các file
server.py            # Entry point – khởi động server
server_handler.py    # Xử lý từng client


Thành viên 2: Khang phụ trách Protocol + User Management
- Thiết kế protocol (JSON):
  - Ví dụ: `{ "type": "login", "user": "A", "msg": "hi" }`
- Login / Logout (ở mức gói tin JSON)
- Quản lý user online (danh sách user đang kết nối)
- Thông báo join / leave (gói tin system message)

Các file
protocol.py        # Định nghĩa JSON protocol, encode/decode message
user_manager.py    # Quản lý user online (username -> ClientHandler)
