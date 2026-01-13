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


# Thành viên 3: Trung Kiên - Client Network Core

## Mô tả Task

Phát triển phần **Client Network Core**, bao gồm:
- Kết nối socket tới server
- Gửi và nhận message
- Thread xử lý nhận dữ liệu liên tục
- Xử lý reconnect khi mất kết nối
- Error handling (username trùng, mất kết nối)

---

## Cấu trúc File

```
App_Chat_Socket/
└── Client/
    ├── protocol.py          # Protocol JSON (copy từ Server)
    ├── client_network.py    # Core network layer
    └── client.py            # Console client (để test)
```

---

## File 1: `client_network.py`

### Chức năng chính

| Phương thức | Mô tả |
|-------------|-------|
| `connect()` | Kết nối socket tới server |
| `disconnect()` | Ngắt kết nối |
| `send_login()` | Gửi gói login |
| `send_logout()` | Gửi gói logout |
| `send_message()` | Gửi message chat |
| `reconnect()` | Thử kết nối lại khi bị disconnect |
| `_receive_loop()` | Thread nhận dữ liệu liên tục |
| `_process_message()` | Xử lý message nhận được |

### Đặc điểm kỹ thuật

- **Socket**:  TCP (`socket. SOCK_STREAM`)
- **Protocol**: JSON (dùng `protocol.py`)
- **Delimiter**: `\n` (newline) để phân tách message
- **Threading**: Thread riêng cho việc nhận dữ liệu
- **Callback**: Hỗ trợ callback `on_message` và `on_disconnect`

### Code snippet quan trọng

```python
# Kết nối
self.socket = socket.socket(socket.AF_INET, socket. SOCK_STREAM)
self.socket.connect((self.host, self.port))

# Gửi message với delimiter
raw_bytes = encode_message(data)
self.socket.sendall(raw_bytes + b'\n')

# Nhận message với buffer
buffer = b""
while b'\n' in buffer:
    line, buffer = buffer.split(b'\n', 1)
    self._process_message(line)
```

---

## File 2: `client.py`

### Chức năng

Console client đơn giản để test network core: 
- Nhập username
- Kết nối tới server
- Gửi/nhận message qua console
- Xử lý disconnect và hỏi reconnect
---

## Kiến trúc

```
┌─────────────────┐
│   client. py     │  ← Console UI (test)
│   (Main App)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│client_network.py│  ← Network Core Layer
│  (Socket + API) │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  protocol.py    │  ← JSON Protocol
│ (encode/decode) │
└────────┬────────┘
         │
         ↓
    [TCP Socket]
         │
         ↓
┌─────────────────┐
│     Server      │
└─────────────────┘
```

---

## 🔄 Thay đổi trong Server (Để tương thích với Client)

### 🔧 File:  `server_handler.py`

#### **❌ Vấn đề của version cũ:**

1. **Không dùng Protocol JSON** → Chỉ gửi/nhận string thuần
2. **Không có delimiter** (`\n`) → Client không biết khi nào message kết thúc
3. **Không có user manager** → Không quản lý username trùng
4. **Không phân loại message** → Không có `type`, `timestamp`
5. **Không xử lý buffer** → Nhận message từng lần `recv(1024)`

### 📊 So sánh thay đổi `server_handler.py`

| Tính năng               | Version cũ                 | Version mới |
|-------------------------|----------------------------|-------------|
| **Protocol**            | ❌ String thuần            | ✅ JSON |
| **Delimiter**           | ❌ Không có                | ✅ `\n` |
| **Buffer**              | ❌ `recv(1024)` trực tiếp  | ✅ Buffer + split `\n` |
| **Message type**        | ❌ Không phân loại         | ✅ `login`, `logout`, `message` |
| **Timestamp**           | ❌ Không có                | ✅ Tự động thêm |
| **Username validation** | ❌ Không kiểm tra          | ✅ Kiểm tra trùng |
| **User management**     | ❌ Không có                | ✅ Dùng `UserManager` |
| **User list**           | ❌ Không gửi               | ✅ Broadcast khi có thay đổi |
| **Error handling**      | ❌ Chỉ print               | ✅ Gửi error message về client |

---

### ✅ Đã hoàn thành

- [x] Kết nối TCP socket
- [x] Gửi/nhận message với Protocol JSON
- [x] Thread riêng cho receive loop
- [x] Xử lý buffer với delimiter `\n`
- [x] Callback architecture (on_message, on_disconnect)
- [x] Reconnect mechanism
- [x] Error handling đầy đủ
- [x] Support tiếng Việt & emoji
- [x] Console client để test

---

## Tích hợp với 2 thành viên trước

### Server Core + Protocol

Client sử dụng: 
- ✅ `protocol.py` - Encode/decode JSON
- ✅ Server API (login, logout, message)
- ✅ Message format chuẩn

---

## Kết luận

Task **Thành viên 3 - Client Network Core** đã hoàn thành đầy đủ các yêu cầu: 

✅ **Client socket** - Kết nối TCP tới server  
✅ **Gửi/nhận message** - Protocol JSON đầy đủ  
✅ **Thread nhận dữ liệu** - Receive loop liên tục  
✅ **Reconnect** - Tự động hoặc thủ công  
✅ **Error handling** - Username, disconnect, invalid message  