import threading

class ClientHandler(threading.Thread):
    def __init__(self, client_socket, address, server):
        super().__init__()
        self.client_socket = client_socket
        self.address = address
        self.server = server
        self.username = None
        self.running = True
        
    def run(self):
        """Thread chính xử lý client"""
        try:
            # Nhận username từ client
            self.username = self.client_socket.recv(1024).decode('utf-8')
            
            # Thông báo user mới join
            join_msg = f"[SERVER] {self.username} đã tham gia chat!"
            print(join_msg)
            self.server.broadcast(join_msg, self)
            
            # Gửi welcome message
            welcome = f"[SERVER] Chào mừng {self.username}!"
            self.send_message(welcome)
            
            # Nhận và xử lý messages
            while self.running:
                try:
                    message = self.client_socket.recv(1024).decode('utf-8')
                    
                    if message:
                        formatted_msg = f"{self.username}: {message}"
                        print(f"[MESSAGE] {formatted_msg}")
                        
                        # Broadcast đến tất cả clients khác
                        self.server.broadcast(formatted_msg, self)
                    else:
                        # Client đã disconnect
                        break
                        
                except Exception as e:
                    print(f"[LỖI] Lỗi khi nhận message từ {self.username}: {e}")
                    break
                    
        except Exception as e:
            print(f"[LỖI] Lỗi với client {self.address}: {e}")
        
        finally:
            self.close()
    
    def send_message(self, message):
        """Gửi message đến client này"""
        try:
            self.client_socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"[LỖI] Không thể gửi message đến {self.username}: {e}")
            raise
    
    def close(self):
        """Đóng kết nối và cleanup"""
        self.running = False
        
        if self.username:
            # Thông báo user rời khỏi
            leave_msg = f"[SERVER] {self.username} đã rời khỏi chat."
            print(leave_msg)
            self.server.broadcast(leave_msg, self)
        
        # Xóa khỏi danh sách clients
        self.server.remove_client(self)
        
        # Đóng socket
        try:
            self.client_socket.close()
        except:
            pass