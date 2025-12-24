using System;
using System.Text;
using System.Threading.Tasks;
using System.Net;
using System.Net.Sockets;
using System.IO;

namespace TCP_Server
{
    internal class TCP_EchoServer
    {
        public static async Task Main(string[] args)
        {
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            Console.InputEncoding = System.Text.Encoding.UTF8;
            string severHost = "127.0.0.1";
            int serverPort = 5000;
            var listener = new TcpListener(IPAddress.Parse("127.0.0.1"), port: serverPort);
            listener.Start();
            Console.WriteLine($"Đang chờ kết nói đến {severHost} với port:{serverPort}");

            while (true)
            {
                var client = await listener.AcceptTcpClientAsync();
                Console.WriteLine("Đã có kết nối từ " + client.Client.RemoteEndPoint);
                _ = HandleClientAsync(client);
            }

        }
        private static async Task HandleClientAsync(TcpClient client)
        {

            using (client)
            using (NetworkStream stream = client.GetStream())
            {
                
                byte[] buffer = new byte[1024];
                try
                {
                    while (true) 
                    {
                    //đọc tin nhắn từ client
                    int byteRead = await stream.ReadAsync(buffer, 0, buffer.Length);
                    if (byteRead == 0)
                    {
                        Console.WriteLine("Client đã ngắt kết nối.");
                        break;
                    }
                    string data = Encoding.UTF8.GetString(buffer, 0, byteRead);
                    Console.WriteLine("Tin nhắn từ Client: " + data);

                    // gửi phản hồi đến client
                    byte[] responseData = Encoding.UTF8.GetBytes(data);
                    await stream.WriteAsync(responseData, 0, responseData.Length);
                    Console.WriteLine("Gửi phản hồi đến Client: " + data);
                    }
                }
                catch (IOException ex)
                {
                    Console.WriteLine("Kết nối lỗi/đã bị ngắt: " + ex.Message);

                }

            }
            Console.WriteLine("Server quay lại chờ kết nối mới...");
        }
    }
}
