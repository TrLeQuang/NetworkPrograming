using System;
using System.Net.Sockets;
using System.Text;
using RockPaperScissorsServer.Protocol;

namespace RockPaperScissorsServer.Network
{
    public class ClientHandler
    {
        private TcpClient client;
        private NetworkStream stream;
        private IServerService serverService;

        public ClientHandler Partner { get; set; }
        public bool HasMadeChoice { get; set; }
        public string CurrentChoice { get; set; }
        public string ClientId { get; private set; }

        private static int clientCounter = 0;

        public ClientHandler(TcpClient client, IServerService serverService)
        {
            this.client = client;
            this.serverService = serverService;
            this.stream = client.GetStream();
            this.Partner = null;
            this.HasMadeChoice = false;
            this.CurrentChoice = null;
            this.ClientId = $"C{++clientCounter}";
        }

        public void Handle()
        {
            try
            {
                byte[] buffer = new byte[1024];
                while (true)
                {
                    int bytesRead = stream.Read(buffer, 0, buffer.Length);
                    if (bytesRead == 0) break;

                    string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    ProcessMessage(message);
                }
            }
            catch (Exception ex)
            {
                serverService.LogMessage($"⚠ Error handling client {ClientId}: {ex.Message}");
            }
            finally
            {
                Disconnect();
            }
        }

        private void ProcessMessage(string message)
        {
            if (ProtocolMessage.Parser.TryParsePlay(message, out string choice))
            {
                serverService.ProcessGame(this, choice);
            }
        }

        public void SendMessage(string message)
        {
            try
            {
                byte[] data = Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);
            }
            catch (Exception ex)
            {
                serverService.LogMessage($"⚠ Error sending message to {ClientId}: {ex.Message}");
            }
        }

        public void Disconnect()
        {
            try
            {
                stream?.Close();
                client?.Close();
            }
            catch { }

            serverService.RemoveClient(this);
        }
    }

    // Interface để tránh circular dependency
    public interface IServerService
    {
        void ProcessGame(ClientHandler player, string choice);
        void RemoveClient(ClientHandler client);
        void LogMessage(string message);
    }
}
