using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace TCP_Client
{
    internal class TCP_Client
    {
        public static async Task Main(string[] args)
        {
            Console.OutputEncoding = Encoding.UTF8;
            Console.InputEncoding = Encoding.UTF8;

            string clientHost = "127.0.0.1";
            int clientPort = 8889;

            using var client = new TcpClient();
            await client.ConnectAsync(IPAddress.Parse(clientHost), clientPort);
            Console.WriteLine($"Đã kết nối đến server {clientHost}:{clientPort}");

            using NetworkStream stream = client.GetStream();
            using var reader = new StreamReader(stream, Encoding.UTF8, leaveOpen: true);
            using var writer = new StreamWriter(stream, Encoding.UTF8, leaveOpen: true) { AutoFlush = true };

            // Task nhận tin nhắn từ server
            var receiveTask = Task.Run(async () =>
            {
                while (true)
                {
                    string? line = await reader.ReadLineAsync();
                    if (line == null) break;
                    Console.WriteLine(line);
                }

                Console.WriteLine("Server ngắt kết nối.");
            });

            // Gửi tin nhắn từ bàn phím
            while (true)
            {
                string? msg = Console.ReadLine();
                if (msg == null) break;

                await writer.WriteLineAsync(msg);

                if (msg.Trim().Equals("/quit", StringComparison.OrdinalIgnoreCase))
                    break;
            }

            // chờ task nhận kết thúc
            await receiveTask;
        }
    }
}