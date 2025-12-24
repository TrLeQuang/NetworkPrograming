# UDP Chat – Demo tối ưu UDP (Python, GUI)

## 1. Mục tiêu bài tập
Ứng dụng này được xây dựng nhằm **mô phỏng và minh họa các kỹ thuật tối ưu hóa UDP**
trong một ứng dụng chat đơn giản có giao diện đồ họa (GUI).

Ứng dụng không hướng tới triển khai thực tế, mà phục vụ cho mục đích học tập
trong môn **Lập trình mạng**.

---

## 2. Kiến trúc tổng thể

Ứng dụng hoạt động theo mô hình **Client – Server**:

- **Server**:  
  - Chạy dưới dạng console  
  - Nhận và phân phối (broadcast) tin nhắn cho các client  
  - Xử lý UDP và mô phỏng các đặc tính không tin cậy của UDP  

- **Client**:  
  - Có giao diện GUI (Tkinter)  
  - Cho phép người dùng nhập tên, kết nối server và chat trực tiếp  
  - Bên dưới GUI là cơ chế UDP có ACK và gửi lại (retransmission)

---

## 3. Các kỹ thuật tối ưu UDP được mô phỏng

Ứng dụng minh họa các kỹ thuật sau:

- **Packet Sequencing**:  
  Mỗi gói tin chat được gắn số thứ tự (sequence number).

- **ACK (Acknowledgement)**:  
  Server gửi gói xác nhận (ACK) cho mỗi gói tin nhận thành công.

- **Retransmission**:  
  Client tự động gửi lại gói tin nếu không nhận được ACK trong thời gian timeout.

- **Deduplication**:  
  Server và client loại bỏ các gói tin trùng lặp khi resend.

- **Packet Loss Simulation**:  
  Có thể giả lập mất gói bằng cách chỉnh `LOSS_RATE` trong file `Config.py`.

---

## 4. Cấu trúc thư mục

UDP/
│
├── Server.py # Server chat (console)
├── Client.py # Client chat có GUI
├── Reliable_UDP.py # Lớp UDP có ACK + resend
├── Protocol.py # Định dạng gói tin
├── Config.py # Cấu hình (IP, Port, LOSS_RATE, timeout)
└── README.md

## 5. Cách chạy chương trình

Ứng dụng được chạy **hoàn toàn bằng phím F5 trong Visual Studio**.

### Bước 1: Chạy Server
1. Mở **Visual Studio (lần 1)**
2. Chuột phải `Server.py`
3. Chọn **Set as Startup File**
4. Bấm **F5**
5. Server hiển thị: UDP Chat Server chạy tại 127.0.0.1:9000

### Bước 2: Chạy Client A
1. Mở **Visual Studio (lần 2)**
2. Mở cùng project
3. Chuột phải `Client.py`
4. Chọn **Set as Startup File**
5. Bấm **F5**
6. Nhập tên (ví dụ: A) → bấm **Kết nối**

### Bước 3: Chạy Client B
1. Mở **Visual Studio (lần 3)**
2. Mở cùng project
3. Chuột phải `Client.py`
4. Chọn **Set as Startup File**
5. Bấm **F5**
6. Nhập tên (ví dụ: B) → bấm **Kết nối**

---

## 6. Cách demo chat

- Client A gửi tin nhắn → Client B nhận được
- Client B gửi tin nhắn → Client A nhận được
- Server console hiển thị log nhận và broadcast tin nhắn

Ứng dụng cho phép mở **nhiều client GUI cùng lúc**.

---

## 7. Về việc hiển thị tin nhắn

- Khi người dùng bấm **Gửi**, client sẽ hiển thị ngay tin nhắn của chính mình
(local echo) để tăng trải nghiệm người dùng.
- Tin nhắn sau đó được gửi lên server và broadcast đến các client khác.
- Vì vậy, mỗi client:
- Thấy tin nhắn của mình
- Thấy tin nhắn của các client khác
- Cách hiển thị này tương tự các ứng dụng chat thực tế.

---

## 8. Mô phỏng mất gói UDP

Trong file `Config.py`, nếu nhập:

LOSS_RATE = 0.0
→ Chat ổn định, không có cảnh báo gửi thất bại.

LOSS_RATE > 0 (ví dụ nhập LOSS_RATE = 0.3)
→ Xuất hiện resend, timeout và có thể có cảnh báo gửi thất bại.
→ Phản ánh đúng đặc tính không tin cậy của UDP.

Thông báo “Gửi thất bại sau nhiều lần thử” không phải lỗi chương trình,
mà là kết quả của mô phỏng UDP khi gói tin hoặc ACK không được xác nhận.
Việc mở nhiều Visual Studio cùng lúc là cần thiết để mô phỏng nhiều client.

