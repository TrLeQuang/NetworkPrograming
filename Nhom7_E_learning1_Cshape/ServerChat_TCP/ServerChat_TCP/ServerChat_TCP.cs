using System;
using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading.Tasks;

namespace ServerChat
{
    internal class ServerChat
    {
        private static readonly ConcurrentDictionary<int, ClientState> Clients = new();
        private static int NextClientId = 0;
        public static async Task Main(string[] args)
        {
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            Console.InputEncoding = System.Text.Encoding.UTF8;

            string severHost = "127.0.0.1";
            int serverPort = 8888;

            var listener = new TcpListener(IPAddress.Parse("127.0.0.1"), port: serverPort);
            listener.Start();
            Console.WriteLine($"Đang chờ kết nói đến {severHost} với port:{serverPort}");

            while (true) {
                var tcpClient = await listener.AcceptTcpClientAsync();
                int id = System.Threading.Interlocked.Increment(ref NextClientId);
                Console.WriteLine($"Client{id} đã kết nối đến:{tcpClient.Client.RemoteEndPoint}");

                var state = new ClientState(id, tcpClient);
                Clients.TryAdd(id, state);

                _ = HandleClientAsync(state); // chạy song song
            }

        }

        private static async Task HandleClientAsync(ClientState client)
        {
            try
            {
                using (client.TcpClient)
                using (NetworkStream stream = client.TcpClient.GetStream())
                using (var reader = new StreamReader(stream, Encoding.UTF8, leaveOpen: true))
                using (var writer = new StreamWriter(stream, Encoding.UTF8, leaveOpen: true) { AutoFlush = true })
                {
                    client.Writer = writer;

                    // chào client mới
                    await writer.WriteLineAsync($"Welcome! You are Client#{client.Id}. Type /name <yourname> to set name.");
                    await BroadcastAsync($"Client#{client.Id} joined.", exceptClientId: client.Id);

                    while (true)
                    {
                        // đọc 1 dòng (1 message)
                        string? line = await reader.ReadLineAsync();
                        if (line == null)
                        {
                            // client đóng kết nối
                            break;
                        }

                        line = line.Trim();
                        if (line.Length == 0) continue;

                        // command đổi tên
                        if (line.StartsWith("/name ", StringComparison.OrdinalIgnoreCase))
                        {
                            string newName = line.Substring(6).Trim();
                            if (newName.Length == 0)
                            {
                                await writer.WriteLineAsync("Usage: /name <yourname>");
                                continue;
                            }

                            string old = client.DisplayName;
                            client.DisplayName = newName;
                            await writer.WriteLineAsync($"Your name is now: {client.DisplayName}");
                            await BroadcastAsync($"{old} is now {client.DisplayName}", exceptClientId: client.Id);
                            continue;
                        }

                        // command thoát
                        if (line.Equals("/quit", StringComparison.OrdinalIgnoreCase))
                        {
                            await writer.WriteLineAsync("Bye!");
                            break;
                        }

                        // broadcast tin nhắn
                        string msg = $"{client.DisplayName}: {line}";
                        Console.WriteLine(msg);
                        await BroadcastAsync(msg, exceptClientId: client.Id);
                    }
                }
            }
            catch (IOException ex)
            {
                Console.WriteLine($"Client#{client.Id} IO error: {ex.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Client#{client.Id} error: {ex}");
            }
            finally
            {
                Clients.TryRemove(client.Id, out _);
                Console.WriteLine($"Client#{client.Id} disconnected");
                await BroadcastAsync($"{client.DisplayName} left.");
            }
        }
        private static async Task BroadcastAsync(string message, int? exceptClientId = null)
        {
            foreach (var kv in Clients)
            {
                int id = kv.Key;
                var c = kv.Value;

                if (exceptClientId.HasValue && id == exceptClientId.Value)
                    continue;

                var w = c.Writer;
                if (w == null) continue;

                try
                {
                    await w.WriteLineAsync(message);
                }
                catch
                {
                    // nếu gửi fail thì bỏ qua (client có thể vừa ngắt)
                }
            }
        }

        private sealed class ClientState
        {
            public int Id { get; }
            public TcpClient TcpClient { get; }
            public StreamWriter? Writer { get; set; }
            public string DisplayName { get; set; }

            public ClientState(int id, TcpClient tcpClient)
            {
                Id = id;
                TcpClient = tcpClient;
                DisplayName = $"Client#{id}";
            }
        }
    }
}

