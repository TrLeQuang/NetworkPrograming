using System;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using RockPaperScissorsClient.Protocol;

namespace RockPaperScissorsClient.Network
{
    public class ClientConnection
    {
        private TcpClient client;
        private NetworkStream stream;
        private bool isConnected = false;
        private Thread receiveThread;
        private IClientMessageHandler messageHandler;

        public bool IsConnected => isConnected;

        public ClientConnection(IClientMessageHandler messageHandler)
        {
            this.messageHandler = messageHandler;
        }

        public bool Connect(string serverIp, int port)
        {
            try
            {
                client = new TcpClient();
                client.Connect(serverIp, port);
                stream = client.GetStream();
                isConnected = true;

                receiveThread = new Thread(ReceiveMessages);
                receiveThread.IsBackground = true;
                receiveThread.Start();

                return true;
            }
            catch (Exception ex)
            {
                messageHandler.OnConnectionError($"Connection error: {ex.Message}");
                return false;
            }
        }

        public void Disconnect()
        {
            isConnected = false;

            try
            {
                stream?.Close();
                client?.Close();
            }
            catch { }

            messageHandler.OnDisconnected();
        }

        public bool SendChoice(string choice)
        {
            try
            {
                string message = ProtocolMessage.Builder.Play(choice);
                byte[] data = Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);
                return true;
            }
            catch (Exception ex)
            {
                messageHandler.OnConnectionError($"Error sending choice: {ex.Message}");
                return false;
            }
        }

        private void ReceiveMessages()
        {
            byte[] buffer = new byte[1024];

            while (isConnected)
            {
                try
                {
                    int bytesRead = stream.Read(buffer, 0, buffer.Length);
                    if (bytesRead == 0)
                    {
                        break;
                    }

                    string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    messageHandler.OnMessageReceived(message);
                }
                catch (Exception)
                {
                    break;
                }
            }

            if (isConnected)
            {
                Disconnect();
            }
        }
    }

    public interface IClientMessageHandler
    {
        void OnMessageReceived(string message);
        void OnDisconnected();
        void OnConnectionError(string error);
    }
}