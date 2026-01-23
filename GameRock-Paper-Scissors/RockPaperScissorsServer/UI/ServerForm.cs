using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Windows.Forms;
using RockPaperScissorsServer.Network;
using RockPaperScissorsServer.Matchmaking;
using RockPaperScissorsServer.Game;
using RockPaperScissorsServer.Protocol;

namespace RockPaperScissorsServer.UI
{
    public partial class ServerForm : Form, IServerService
    {
        private TcpListener server;
        private List<ClientHandler> clients = new List<ClientHandler>();
        private Matchmaker matchmaker = new Matchmaker();
        private bool isRunning = false;

        // UI Controls
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
            matchmaker.Clear();

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
                    bool paired = matchmaker.TryPairClient(handler, clients);

                    if (paired)
                    {
                        var partner = handler.Partner;
                        LogMessage($"🔗 Paired: Player {partner.ClientId} ↔ Player {handler.ClientId}");
                    }
                    else
                    {
                        LogMessage($"⏳ Player {handler.ClientId} is waiting for a partner...");
                    }

                    UpdatePlayerCount();
                    BroadcastPlayerCount();
                }
                catch (Exception ex)
                {
                    if (isRunning)
                    {
                        LogMessage($"⚠ Error accepting client: {ex.Message}");
                    }
                }
            }
        }

        public void RemoveClient(ClientHandler client)
        {
            clients.Remove(client);
            matchmaker.RemovePair(client);

            var partner = client.Partner;
            if (partner != null)
            {
                LogMessage($"⚠ Player {partner.ClientId}'s opponent disconnected");
            }

            LogMessage($"← Client disconnected (ID: {client.ClientId})");
            UpdatePlayerCount();
            BroadcastPlayerCount();
        }

        public void ProcessGame(ClientHandler player, string choice)
        {
            if (player.Partner == null)
            {
                player.SendMessage(ProtocolMessage.Builder.Waiting(
                    "You don't have a partner yet. Waiting for another player..."));
                LogMessage($"⚠ Player {player.ClientId} tried to play without a partner");
                return;
            }

            if (!GameLogic.IsValidChoice(choice))
            {
                LogMessage($"⚠ Player {player.ClientId} sent invalid choice: {choice}");
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

                string result1 = GameLogic.DetermineWinner(choice1, choice2);
                string result2 = GameLogic.GetOppositeResult(result1);

                player.SendMessage(ProtocolMessage.Builder.Result(result1, choice1, choice2));
                partner.SendMessage(ProtocolMessage.Builder.Result(result2, choice2, choice1));

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
                player.SendMessage(ProtocolMessage.Builder.Waiting(
                    "Waiting for your opponent to make a choice..."));
                partner.SendMessage(ProtocolMessage.Builder.OpponentStatus(ProtocolMessage.STATUS_WAITING));
                LogMessage($"⏳ Player {player.ClientId} is waiting for Player {partner.ClientId}");
            }
        }

        private void BroadcastPlayerCount()
        {
            string message = ProtocolMessage.Builder.PlayerCount(clients.Count);
            foreach (var client in clients.ToList())
            {
                client.SendMessage(message);
            }
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
                lblPlayerCount.Text = $"Connected Players: {clients.Count} (Pairs: {matchmaker.PairCount})";
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
}