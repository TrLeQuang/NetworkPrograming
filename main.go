package main

import (
	"bufio" //đọc và ghi dữ liệu có bộ đệm
	"context"
	"fmt"     //In chuỗi, định dạng dữ liệu
	"log"     //ghi log ra màn hình
	"net"     //làm việc với TCP/IP
	"runtime" //Điều khiển CPU, goroutine
	"syscall" //Can thiệp sâu vào socket
	"time"    //xử lý thời gian
)

const (
	ADDR        = ":9000"         //cổng server TCP
	BUFFER_SIZE = 4 * 1024 * 1024 //kích thước buffer = 4MB
)

func main() {
	runtime.GOMAXPROCS(runtime.NumCPU()) //NumCPU() là đếm số lõi CPU, GOMAXPROCS() cho phép Go dùng toàn bộ CPU

	lc := net.ListenConfig{
		Control: setSocketOptions, //control cho phép thiết lập socket TCP trước khi dùng
	}

	listener, err := lc.Listen(context.Background(), "tcp", ADDR) // dùng giao thức TCP, cổng 9000, đối tượng chờ client kết nối
	if err != nil {
		log.Fatal(err) // nếu mở cổng lỗi thì dừng chương trình
	}
	defer listener.Close()

	log.Println("TCP Server running on", ADDR)
	for {
		conn, err := listener.Accept() // chờ clinet kết nối khi có client thì trả về conn
		if err != nil {                //nếu lỗi thì bỏ qua
			log.Println("Accept error:", err)
			continue
		}
		go handleConnection(conn)
	}

}

func setSocketOptions(network, address string, c syscall.RawConn) error { //tối uu TCP
	return c.Control(func(fd uintptr) {
		syscall.SetsockoptInt(syscall.Handle(fd), syscall.IPPROTO_TCP, syscall.TCP_NODELAY, 1) //gửi dữ liệu ngay lập tức giảm độ trễ
		syscall.SetsockoptInt(syscall.Handle(fd), syscall.SOL_SOCKET, syscall.SO_REUSEADDR, 1) // restart server không bị lỗi chiếm cổng
		syscall.SetsockoptInt(syscall.Handle(fd), syscall.SOL_SOCKET, syscall.SO_RCVBUF, BUFFER_SIZE)
		syscall.SetsockoptInt(syscall.Handle(fd), syscall.SOL_SOCKET, syscall.SO_SNDBUF, BUFFER_SIZE) // Tăng buffer TCP gửi và nhận nhanh hơn
		syscall.SetsockoptInt(syscall.Handle(fd), syscall.SOL_SOCKET, syscall.SO_KEEPALIVE, 1)        // phát hiện client chết
	})
}
func handleConnection(conn net.Conn) { //nhận kết nối cảu client
	defer conn.Close()                                //khi hàm kết thúc tự động đóng kết nối
	conn.SetDeadline(time.Now().Add(5 * time.Minute)) //sau 5phuts không gửi dữ liệu thì ngắt
	reader := bufio.NewReader(conn)
	writer := bufio.NewWriter(conn) //đọc/ghi nhanh hơn
	for {
		msg, err := reader.ReadString('\n') //đọc dữ liệu đến khi gặp ký tự xuống dòng
		if err != nil {                     //client ngắt kết nối thoát hàm
			return
		}
		response := fmt.Sprintf("ACK [%d bytes]\n", len(msg)) // tạo phản hồi cho client
		writer.WriteString(response)
		writer.Flush()
	}

}
