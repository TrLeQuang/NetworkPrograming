using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace LoadTest
{
    internal class Test
    {
        public static async Task Main()
        {
            string host = "127.0.0.1";
            int port = 5000; // đổi sang server bạn muốn test
            int clients = 100;
            int messagesPerClient = 200;

            var sw = Stopwatch.StartNew();

            Task[] tasks = new Task[clients];
            for (int i = 0; i < clients; i++)
            {
                int id = i;
                tasks[i] = RunClientAsync(host, port, id, messagesPerClient);
            }

            await Task.WhenAll(tasks);
            sw.Stop();

            Console.WriteLine($"Done. clients={clients}, messages/client={messagesPerClient}, elapsed={sw.Elapsed}");
        }

        static async Task RunClientAsync(string host, int port, int id, int count)
        {
            using var client = new TcpClient();
            await client.ConnectAsync(IPAddress.Parse(host), port);

            using var stream = client.GetStream();
            using var reader = new StreamReader(stream, Encoding.UTF8, leaveOpen: true);
            using var writer = new StreamWriter(stream, Encoding.UTF8, leaveOpen: true) { AutoFlush = true };

            for (int i = 0; i < count; i++)
            {
                await writer.WriteLineAsync($"client{id}-msg{i}");

                // đọc phản hồi (cho echo server). Nếu test chat server, bạn có thể bỏ đọc hoặc đọc theo logic khác.
                string? resp = await reader.ReadLineAsync();
                if (resp == null) break;
            }

            await writer.WriteLineAsync("/quit");
        }
    }
}