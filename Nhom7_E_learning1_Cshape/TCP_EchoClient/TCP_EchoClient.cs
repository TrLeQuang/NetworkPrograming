using System;
using System.Text;
using System.Threading.Tasks;
using System.Net;
using System.Net.Sockets;
using System.IO;
using System.Runtime.CompilerServices;

namespace TCP_Client
{
    internal class TCP_Client
    {
        public static async Task Main(string[] args)
        {
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            Console.InputEncoding = System.Text.Encoding.UTF8;

            string clientHost = "127.0.0.1";
            int clientPort = 5000;

            var client = new TcpClient();
            client.Connect(IPAddress.Parse(clientHost), clientPort);
            Console.WriteLine($"Đã kết nối đến server {clientHost} với port:{clientPort}");

            using NetworkStream stream = client.GetStream();
            while (true)
            {
                // Gửi tin nhắn đến server
                Console.WriteLine("Gửi lời nhắn đến server");
                string message = Console.ReadLine();
                byte[] data = Encoding.UTF8.GetBytes(message);
                await stream.WriteAsync(data, 0, data.Length);

                // Nhận phản hồi từ server
                byte[] buffer = new byte[1024];
                int byteRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                string response = Encoding.UTF8.GetString(buffer, 0, byteRead);
                Console.WriteLine("Phản hồi từ Server: " + response);
            }
        }
    }

}