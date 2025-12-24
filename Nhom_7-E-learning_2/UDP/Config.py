# Cấu hình chung cho demo UDP Chat

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

BUFFER_SIZE = 4096

# Timeout chờ ACK (giây)
ACK_TIMEOUT = 0.8

# Số lần gửi lại tối đa (để khỏi kẹt vô hạn)
MAX_RETRY = 10

# Giả lập mất gói (0.0 -> 1.0). Ví dụ 0.3 = mất ~30%
LOSS_RATE = 0.5

