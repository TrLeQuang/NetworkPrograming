using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace RockPaperScissorsServer
{
    public partial class ServerForm : Form
    {
        private TcpListener server;
        private List<ClientHandler> clients = new List<ClientHandler>();
        private List<GamePair> gamePairs = new List<GamePair>();
        private bool isRunning = false;
        private TextBox txtLog;
        private Button btnStart;
        private Button btnStop;
        private Label lblStatus;
        private Label lblPlayerCount;

        public ServerForm()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "Rock-Paper-Scissors Server";
            this.Size = new Size(600, 450);
            this.StartPosition = FormStartPosition.CenterScreen;

            lblStatus = new Label
            {
                Text = "Server Status: Stopped",
                Location = new Point(20, 20),
                Size = new Size(300, 25),
                Font = new Font("Arial", 10, FontStyle.Bold),
                ForeColor = Color.Red
            };

            lblPlayerCount = new Label
            {
                Text = "Connected Players: 0",
                Location = new Point(20, 50),
                Size = new Size(300, 25),
                Font = new Font("Arial", 10, FontStyle.Regular)
            };

            btnStart = new Button
            {
                Text = "Start Server",
                Location = new Point(20, 85),
                Size = new Size(120, 35),
                BackColor = Color.LightGreen
            };
            btnStart.Click += BtnStart_Click;

            btnStop = new Button
            {
                Text = "Stop Server",
                Location = new Point(150, 85),
                Size = new Size(120, 35),
                Enabled = false,
                BackColor = Color.LightCoral
            };
            btnStop.Click += BtnStop_Click;

            Label lblLogLabel = new Label
            {
                Text = "Server Log:",
                Location = new Point(20, 130),
                Size = new Size(100, 25),
                Font = new Font("Arial", 9, FontStyle.Bold)
            };

            txtLog = new TextBox
            {
                Location = new Point(20, 155),
                Size = new Size(540, 250),
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                ReadOnly = true,
                BackColor = Color.Black,
                ForeColor = Color.LightGreen,
                Font = new Font("Consolas", 9)
            };

            this.Controls.Add(lblStatus);
            this.Controls.Add(lblPlayerCount);
            this.Controls.Add(btnStart);
            this.Controls.Add(btnStop);
            this.Controls.Add(lblLogLabel);
            this.Controls.Add(txtLog);
        }

        private void BtnStart_Click(object sender, EventArgs e)
        {
            try
            {
                server = new TcpListener(IPAddress.Any, 5000);
                server.Start();
                isRunning = true;

                UpdateStatus("Server Status: Running on port 5000", Color.Green);
                btnStart.Enabled = false;
                btnStop.Enabled = true;

                Thread acceptThread = new Thread(AcceptClients);
                acceptThread.IsBackground = true;
                acceptThread.Start();

                LogMessage("✓ Server started successfully on port 5000!");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error starting server: {ex.Message}");
            }
        }

        private void BtnStop_Click(object sender, EventArgs e)
        {
            isRunning = false;
            server?.Stop();

            foreach (var client in clients.ToList())
            {
                client.Disconnect();
            }
            clients.Clear();
            gamePairs.Clear();

            UpdateStatus("Server Status: Stopped", Color.Red);
            UpdatePlayerCount();
            btnStart.Enabled = true;
            btnStop.Enabled = false;
            LogMessage("✗ Server stopped.");
        }

        private void AcceptClients()
        {
            while (isRunning)
            {
                try
                {
                    TcpClient client = server.AcceptTcpClient();
                    ClientHandler handler = new ClientHandler(client, this);
                    clients.Add(handler);

                    Thread clientThread = new Thread(handler.Handle);
                    clientThread.IsBackground = true;
                    clientThread.Start();

                    LogMessage($"→ New client connected (ID: {handler.ClientId})");

                    // Tự động ghép cặp với client đang chờ
                    TryPairClients(handler);

                    UpdatePlayerCount();
                    BroadcastPlayerCount();
                }
                catch { }
            }
        }

        private void TryPairClients(ClientHandler newClient)
        {
            // Tìm client đang chờ ghép cặp (chưa có partner)
            var waitingClient = clients.FirstOrDefault(c => c != newClient && c.Partner == null);

            if (waitingClient != null)
            {
                // Ghép cặp hai client
                GamePair pair = new GamePair(waitingClient, newClient);
                gamePairs.Add(pair);

                waitingClient.Partner = newClient;
                newClient.Partner = waitingClient;

                waitingClient.SendMessage("OPPONENT_STATUS|PAIRED");
                newClient.SendMessage("OPPONENT_STATUS|PAIRED");

                LogMessage($"🔗 Paired: Player {waitingClient.ClientId} ↔ Player {newClient.ClientId}");
            }
            else
            {
                // Không có ai chờ, client này sẽ chờ người tiếp theo
                newClient.SendMessage("WAITING|Waiting for another player to join...");
                LogMessage($"⏳ Player {newClient.ClientId} is waiting for a partner...");
            }
        }

        public void RemoveClient(ClientHandler client)
        {
            clients.Remove(client);

            // Xóa cặp game nếu có
            var pair = gamePairs.FirstOrDefault(p => p.Player1 == client || p.Player2 == client);
            if (pair != null)
            {
                gamePairs.Remove(pair);

                // Thông báo cho partner rằng đối thủ đã disconnect
                var partner = client.Partner;
                if (partner != null)
                {
                    partner.Partner = null;
                    partner.SendMessage("OPPONENT_STATUS|DISCONNECTED");
                    LogMessage($"⚠ Player {partner.ClientId}'s opponent disconnected");
                }
            }

            LogMessage($"← Client disconnected (ID: {client.ClientId})");
            UpdatePlayerCount();
            BroadcastPlayerCount();
        }

        public void ProcessGame(ClientHandler player, string choice)
        {
            if (player.Partner == null)
            {
                player.SendMessage("WAITING|You don't have a partner yet. Waiting for another player...");
                LogMessage($"⚠ Player {player.ClientId} tried to play without a partner");
                return;
            }

            var partner = player.Partner;

            // Lưu lựa chọn của player hiện tại
            player.CurrentChoice = choice;
            player.HasMadeChoice = true;

            LogMessage($"→ Player {player.ClientId} chose: {choice}");

            // Kiểm tra xem partner đã chọn chưa
            if (partner.HasMadeChoice)
            {
                // Cả hai đã chọn, xử lý kết quả
                string choice1 = player.CurrentChoice;
                string choice2 = partner.CurrentChoice;

                string result1 = DetermineWinner(choice1, choice2);
                string result2 = GetOppositeResult(result1);

                player.SendMessage($"RESULT|{result1}|You: {choice1}, Opponent: {choice2}");
                partner.SendMessage($"RESULT|{result2}|You: {choice2}, Opponent: {choice1}");

                LogMessage($"⚔ Game: Player {player.ClientId} ({choice1}) vs Player {partner.ClientId} ({choice2}) → Result: {result1}/{result2}");

                // Reset trạng thái cho lượt tiếp theo
                player.HasMadeChoice = false;
                player.CurrentChoice = null;
                partner.HasMadeChoice = false;
                partner.CurrentChoice = null;
            }
            else
            {
                // Partner chưa chọn, thông báo đợi
                player.SendMessage("WAITING|Waiting for your opponent to make a choice...");
                partner.SendMessage("OPPONENT_STATUS|WAITING");
                LogMessage($"⏳ Player {player.ClientId} is waiting for Player {partner.ClientId}");
            }
        }

        private void BroadcastPlayerCount()
        {
            string message = $"PLAYER_COUNT|{clients.Count}";
            foreach (var client in clients.ToList())
            {
                client.SendMessage(message);
            }
        }

        private string DetermineWinner(string choice1, string choice2)
        {
            if (choice1 == choice2) return "DRAW";
            if ((choice1 == "ROCK" && choice2 == "SCISSORS") ||
                (choice1 == "PAPER" && choice2 == "ROCK") ||
                (choice1 == "SCISSORS" && choice2 == "PAPER"))
                return "WIN";
            return "LOSE";
        }

        private string GetOppositeResult(string result)
        {
            if (result == "WIN") return "LOSE";
            if (result == "LOSE") return "WIN";
            return "DRAW";
        }

        public void LogMessage(string message)
        {
            if (txtLog.InvokeRequired)
            {
                txtLog.Invoke(new Action(() => LogMessage(message)));
            }
            else
            {
                txtLog.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}\r\n");
            }
        }

        private void UpdateStatus(string status, Color color)
        {
            if (lblStatus.InvokeRequired)
            {
                lblStatus.Invoke(new Action(() => UpdateStatus(status, color)));
            }
            else
            {
                lblStatus.Text = status;
                lblStatus.ForeColor = color;
            }
        }

        private void UpdatePlayerCount()
        {
            if (lblPlayerCount.InvokeRequired)
            {
                lblPlayerCount.Invoke(new Action(UpdatePlayerCount));
            }
            else
            {
                lblPlayerCount.Text = $"Connected Players: {clients.Count} (Pairs: {gamePairs.Count})";
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (isRunning)
            {
                BtnStop_Click(null, null);
            }
            base.OnFormClosing(e);
        }
    }

    public class GamePair
    {
        public ClientHandler Player1 { get; set; }
        public ClientHandler Player2 { get; set; }

        public GamePair(ClientHandler player1, ClientHandler player2)
        {
            Player1 = player1;
            Player2 = player2;
        }
    }

    public class ClientHandler
    {
        private TcpClient client;
        private NetworkStream stream;
        private ServerForm server;
        public ClientHandler Partner { get; set; }
        public bool HasMadeChoice { get; set; }
        public string CurrentChoice { get; set; }
        public string ClientId { get; private set; }
        private static int clientCounter = 0;

        public ClientHandler(TcpClient client, ServerForm server)
        {
            this.client = client;
            this.server = server;
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

                    if (message.StartsWith("PLAY|"))
                    {
                        string choice = message.Split('|')[1];
                        server.ProcessGame(this, choice);
                    }
                }
            }
            catch { }
            finally
            {
                Disconnect();
            }
        }

        public void SendMessage(string message)
        {
            try
            {
                byte[] data = Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);
            }
            catch { }
        }

        public void Disconnect()
        {
            stream?.Close();
            client?.Close();
            server.RemoveClient(this);
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new ServerForm());
        }
    }
}