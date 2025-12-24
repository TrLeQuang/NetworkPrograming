using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;

class UdpEchoServerSelect
{
    static void Main(string[] args)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        Console.InputEncoding = System.Text.Encoding.UTF8;  
        int port = args.Length > 0 ? int.Parse(args[0]) : 9999;

        using var sock = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp);

        // Bind server port cố định
        sock.Bind(new IPEndPoint(IPAddress.Any, port));

        // Non-blocking socket
        sock.Blocking = false;

        Console.WriteLine($"UDP server đang lắng nghe 0.0.0.0:{port}");

        // Reuse lists để tránh cấp phát liên tục
        var readList = new List<Socket>(capacity: 1);

        // Buffer nhận (UDP 1 datagram -> 1 message)
        byte[] buffer = new byte[2048];

        while (true)
        {
            readList.Clear();
            readList.Add(sock);

            // Timeout tính bằng microseconds. 100_000 = 100ms
            Socket.Select(readList, null, null, 100_000);

            if (readList.Count == 0)
            {
                // không có dữ liệu, loop tiếp (có thể làm việc khác ở đây)
                continue;
            }

            // Có thể có nhiều datagram đang chờ; đọc cho “cạn” để giảm latency
            while (true)
            {
                EndPoint remote = new IPEndPoint(IPAddress.Any, 0);

                int n;
                try
                {
                    n = sock.ReceiveFrom(buffer, 0, buffer.Length, SocketFlags.None, ref remote);
                }
                catch (SocketException ex) when (ex.SocketErrorCode == SocketError.WouldBlock)
                {
                    // Không còn datagram nào đang chờ
                    break;
                }

                // Echo lại đúng số byte nhận
                try
                {
                    sock.SendTo(buffer, 0, n, SocketFlags.None, remote);
                }
                catch (SocketException ex)
                {
                    Console.WriteLine($"SendTo error: {ex.SocketErrorCode}");
                }
            }
        }
    }
}