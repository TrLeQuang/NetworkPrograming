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
                    UpdatePlayerCount();
                    BroadcastPlayerCount();
                }
                catch { }
            }
        }

        public void RemoveClient(ClientHandler client)
        {
            clients.Remove(client);
            LogMessage($"← Client disconnected (ID: {client.ClientId})");
            UpdatePlayerCount();
            BroadcastPlayerCount();
        }

        public void ProcessGame(ClientHandler player1, string choice1)
        {
            // Tìm người chơi đang chờ (không phải chính mình)
            var waitingPlayer = clients.FirstOrDefault(c => c != player1 && c.IsWaiting);

            if (waitingPlayer != null)
            {
                string choice2 = waitingPlayer.Choice;
                string result = DetermineWinner(choice1, choice2);

                // Gửi kết quả cho cả hai người chơi
                player1.SendMessage($"RESULT|{result}|You: {choice1}, Opponent: {choice2}");
                waitingPlayer.SendMessage($"RESULT|{GetOppositeResult(result)}|You: {choice2}, Opponent: {choice1}");

                player1.IsWaiting = false;
                waitingPlayer.IsWaiting = false;

                LogMessage($"⚔ Game: Player {player1.ClientId} ({choice1}) vs Player {waitingPlayer.ClientId} ({choice2}) → {result}");
            }
            else
            {
                // Không có đối thủ, đặt vào chế độ chờ
                player1.IsWaiting = true;
                player1.Choice = choice1;
                player1.SendMessage("WAITING|Waiting for opponent to join...");
                LogMessage($"⏳ Player {player1.ClientId} is waiting with choice: {choice1}");

                // Thông báo cho người chơi khác (nếu có) rằng có người đang chờ
                BroadcastOpponentStatus();
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

        private void BroadcastOpponentStatus()
        {
            var waitingPlayer = clients.FirstOrDefault(c => c.IsWaiting);
            bool hasWaiting = waitingPlayer != null;

            string message = $"OPPONENT_STATUS|{(hasWaiting ? "WAITING" : "NONE")}";
            foreach (var client in clients.ToList())
            {
                if (client != waitingPlayer) // Không gửi cho chính người đang chờ
                {
                    client.SendMessage(message);
                }
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
                lblPlayerCount.Text = $"Connected Players: {clients.Count}";
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

    public class ClientHandler
    {
        private TcpClient client;
        private NetworkStream stream;
        private ServerForm server;
        public bool IsWaiting { get; set; }
        public string Choice { get; set; }
        public string ClientId { get; private set; }
        private static int clientCounter = 0;

        public ClientHandler(TcpClient client, ServerForm server)
        {
            this.client = client;
            this.server = server;
            this.stream = client.GetStream();
            this.IsWaiting = false;
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