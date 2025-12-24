using System;
using System.Net;
using System.Net.Sockets;
using System.Text;

class Client_UDP
{
    static void Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;
        Console.InputEncoding = Encoding.UTF8;
        string host = args.Length > 0 ? args[0] : "127.0.0.1";
        int port = args.Length > 1 ? int.Parse(args[1]) : 9999;
        string message = args.Length > 2 ? args[2] : "hello udp";

        using var sock = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp);

        // "Connect" với UDP là pseudo-connect: đặt remote mặc định để dùng Send/Receive
        // Server của bạn vẫn nhận được như bình thường (ReceiveFrom sẽ thấy đúng remote).
        sock.Connect(host, port);

        // Timeout chờ echo (ms)
        sock.ReceiveTimeout = 2000;

        byte[] sendBytes = Encoding.UTF8.GetBytes(message);
        sock.Send(sendBytes);
        Console.WriteLine($"client gửi {host}:{port} với tin nhắn: {message}");

        byte[] buf = new byte[2048];
        try
        {
            int n = sock.Receive(buf); // chỉ nhận datagram từ endpoint đã Connect
            string echo = Encoding.UTF8.GetString(buf, 0, n);
            Console.WriteLine($"echo: {echo}");
        }
        catch (SocketException ex) when (ex.SocketErrorCode == SocketError.TimedOut)
        {
            Console.WriteLine("Hết thời gian chờ");
        }
    }
}