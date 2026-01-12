using System;
using System.Drawing;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace RockPaperScissorsClient
{
    public partial class ClientForm : Form
    {
        private TcpClient client;
        private NetworkStream stream;
        private TextBox txtServer;
        private Button btnConnect;
        private Button btnDisconnect;
        private Button btnRock;
        private Button btnPaper;
        private Button btnScissors;
        private Label lblStatus;
        private Label lblResult;
        private Label lblPlayerCount;
        private Label lblOpponentStatus;
        private TextBox txtLog;
        private bool isConnected = false;

        public ClientForm()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "Rock-Paper-Scissors Client";
            this.Size = new Size(600, 600);
            this.StartPosition = FormStartPosition.CenterScreen;

            // Connection Panel
            Panel connectionPanel = new Panel
            {
                Location = new Point(20, 20),
                Size = new Size(540, 80),
                BorderStyle = BorderStyle.FixedSingle
            };

            Label lblServerLabel = new Label
            {
                Text = "Server IP:",
                Location = new Point(10, 15),
                Size = new Size(80, 25)
            };

            txtServer = new TextBox
            {
                Text = "127.0.0.1",
                Location = new Point(95, 12),
                Size = new Size(150, 25)
            };

            btnConnect = new Button
            {
                Text = "Connect",
                Location = new Point(255, 10),
                Size = new Size(100, 30),
                BackColor = Color.LightGreen
            };
            btnConnect.Click += BtnConnect_Click;

            btnDisconnect = new Button
            {
                Text = "Disconnect",
                Location = new Point(365, 10),
                Size = new Size(100, 30),
                Enabled = false,
                BackColor = Color.LightCoral
            };
            btnDisconnect.Click += BtnDisconnect_Click;

            lblStatus = new Label
            {
                Text = "Status: Not Connected",
                Location = new Point(10, 50),
                Size = new Size(250, 25),
                Font = new Font("Arial", 9, FontStyle.Bold),
                ForeColor = Color.Red
            };

            lblPlayerCount = new Label
            {
                Text = "Players Online: -",
                Location = new Point(270, 50),
                Size = new Size(150, 25),
                Font = new Font("Arial", 9, FontStyle.Regular)
            };

            connectionPanel.Controls.Add(lblServerLabel);
            connectionPanel.Controls.Add(txtServer);
            connectionPanel.Controls.Add(btnConnect);
            connectionPanel.Controls.Add(btnDisconnect);
            connectionPanel.Controls.Add(lblStatus);
            connectionPanel.Controls.Add(lblPlayerCount);

            // Opponent Status
            lblOpponentStatus = new Label
            {
                Text = "Opponent: Waiting for connection...",
                Location = new Point(20, 115),
                Size = new Size(540, 30),
                Font = new Font("Arial", 10, FontStyle.Bold),
                TextAlign = ContentAlignment.MiddleCenter,
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.LightGray
            };

            // Game buttons panel
            Panel gamePanel = new Panel
            {
                Location = new Point(20, 160),
                Size = new Size(540, 120),
                BorderStyle = BorderStyle.FixedSingle
            };

            Label lblChoose = new Label
            {
                Text = "Choose your weapon:",
                Location = new Point(10, 10),
                Size = new Size(200, 25),
                Font = new Font("Arial", 10, FontStyle.Bold)
            };

            btnRock = new Button
            {
                Text = "✊ ROCK",
                Location = new Point(10, 45),
                Size = new Size(160, 60),
                Font = new Font("Arial", 12, FontStyle.Bold),
                BackColor = Color.LightBlue,
                Enabled = false
            };
            btnRock.Click += (s, e) => MakeChoice("ROCK");

            btnPaper = new Button
            {
                Text = "✋ PAPER",
                Location = new Point(190, 45),
                Size = new Size(160, 60),
                Font = new Font("Arial", 12, FontStyle.Bold),
                BackColor = Color.LightGreen,
                Enabled = false
            };
            btnPaper.Click += (s, e) => MakeChoice("PAPER");

            btnScissors = new Button
            {
                Text = "✌ SCISSORS",
                Location = new Point(370, 45),
                Size = new Size(160, 60),
                Font = new Font("Arial", 12, FontStyle.Bold),
                BackColor = Color.LightCoral,
                Enabled = false
            };
            btnScissors.Click += (s, e) => MakeChoice("SCISSORS");

            gamePanel.Controls.Add(lblChoose);
            gamePanel.Controls.Add(btnRock);
            gamePanel.Controls.Add(btnPaper);
            gamePanel.Controls.Add(btnScissors);

            // Result Label
            lblResult = new Label
            {
                Text = "Make your choice to start playing!",
                Location = new Point(20, 290),
                Size = new Size(540, 50),
                Font = new Font("Arial", 14, FontStyle.Bold),
                TextAlign = ContentAlignment.MiddleCenter,
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.White
            };

            // Log
            Label lblLogLabel = new Label
            {
                Text = "Game Log:",
                Location = new Point(20, 350),
                Size = new Size(100, 25)
            };

            txtLog = new TextBox
            {
                Location = new Point(20, 380),
                Size = new Size(540, 170),
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                ReadOnly = true,
                BackColor = Color.Black,
                ForeColor = Color.LightGreen,
                Font = new Font("Consolas", 9)
            };

            this.Controls.Add(connectionPanel);
            this.Controls.Add(lblOpponentStatus);
            this.Controls.Add(gamePanel);
            this.Controls.Add(lblResult);
            this.Controls.Add(lblLogLabel);
            this.Controls.Add(txtLog);
        }

        private void BtnConnect_Click(object sender, EventArgs e)
        {
            try
            {
                client = new TcpClient();
                client.Connect(txtServer.Text, 5000);
                stream = client.GetStream();
                isConnected = true;

                UpdateStatus("Status: Connected", Color.Green);
                btnConnect.Enabled = false;
                btnDisconnect.Enabled = true;
                btnRock.Enabled = true;
                btnPaper.Enabled = true;
                btnScissors.Enabled = true;
                txtServer.Enabled = false;

                Thread receiveThread = new Thread(ReceiveMessages);
                receiveThread.IsBackground = true;
                receiveThread.Start();

                LogMessage("✓ Connected to server!");
                UpdateResult("Ready to play! Choose your weapon.", Color.LightYellow);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Connection error: {ex.Message}", "Error");
            }
        }

        private void BtnDisconnect_Click(object sender, EventArgs e)
        {
            DisconnectFromServer();
        }

        private void DisconnectFromServer()
        {
            isConnected = false;
            stream?.Close();
            client?.Close();

            UpdateStatus("Status: Not Connected", Color.Red);
            UpdatePlayerCount("Players Online: -");
            UpdateOpponentStatus("Opponent: Waiting for connection...", Color.LightGray);
            btnConnect.Enabled = true;
            btnDisconnect.Enabled = false;
            btnRock.Enabled = false;
            btnPaper.Enabled = false;
            btnScissors.Enabled = false;
            txtServer.Enabled = true;
            UpdateResult("Make your choice to start playing!", Color.White);

            LogMessage("✗ Disconnected from server.");
        }

        private void MakeChoice(string choice)
        {
            try
            {
                string message = $"PLAY|{choice}";
                byte[] data = Encoding.UTF8.GetBytes(message);
                stream.Write(data, 0, data.Length);

                btnRock.Enabled = false;
                btnPaper.Enabled = false;
                btnScissors.Enabled = false;

                LogMessage($"→ You chose: {choice}");
                UpdateResult($"Waiting for opponent...", Color.Orange);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error sending choice: {ex.Message}");
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
                    if (bytesRead == 0) break;

                    string message = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    ProcessServerMessage(message);
                }
                catch
                {
                    break;
                }
            }

            if (isConnected)
            {
                DisconnectFromServer();
            }
        }

        private void ProcessServerMessage(string message)
        {
            string[] parts = message.Split('|');

            if (parts[0] == "PLAYER_COUNT")
            {
                int playerCount = int.Parse(parts[1]);
                UpdatePlayerCount($"Players Online: {playerCount}");

                if (playerCount >= 2)
                {
                    LogMessage($"⚡ {playerCount} players online - Ready to play!");
                }
                else
                {
                    LogMessage($"⏳ {playerCount} player online - Waiting for opponent...");
                    UpdateOpponentStatus("Opponent: No one online yet", Color.LightYellow);
                }
            }
            else if (parts[0] == "OPPONENT_STATUS")
            {
                string status = parts[1];
                if (status == "WAITING")
                {
                    UpdateOpponentStatus("Opponent: Ready and waiting! ⚡", Color.LightGreen);
                    LogMessage("⚡ Opponent is ready! Make your move!");
                }
                else
                {
                    UpdateOpponentStatus("Opponent: Available to play", Color.LightBlue);
                }
            }
            else if (parts[0] == "WAITING")
            {
                LogMessage(parts[1]);
                UpdateResult("⏳ Waiting for opponent to join...", Color.Orange);
                UpdateOpponentStatus("Opponent: Waiting for player to join...", Color.LightYellow);
            }
            else if (parts[0] == "RESULT")
            {
                string result = parts[1];
                string details = parts[2];

                Color resultColor = Color.Gray;
                string resultText = "";

                if (result == "WIN")
                {
                    resultColor = Color.LightGreen;
                    resultText = "🎉 YOU WIN! 🎉";
                }
                else if (result == "LOSE")
                {
                    resultColor = Color.LightCoral;
                    resultText = "😞 YOU LOSE!";
                }
                else
                {
                    resultColor = Color.LightBlue;
                    resultText = "🤝 IT'S A DRAW!";
                }

                UpdateResult(resultText, resultColor);
                LogMessage($"⚔ Game Result: {resultText}");
                LogMessage($"   Details: {details}");

                EnableButtons();
                UpdateOpponentStatus("Opponent: Available for another round", Color.LightBlue);
            }
        }

        private void EnableButtons()
        {
            if (btnRock.InvokeRequired)
            {
                btnRock.Invoke(new Action(EnableButtons));
            }
            else
            {
                btnRock.Enabled = true;
                btnPaper.Enabled = true;
                btnScissors.Enabled = true;
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

        private void UpdatePlayerCount(string text)
        {
            if (lblPlayerCount.InvokeRequired)
            {
                lblPlayerCount.Invoke(new Action(() => UpdatePlayerCount(text)));
            }
            else
            {
                lblPlayerCount.Text = text;
            }
        }

        private void UpdateOpponentStatus(string text, Color color)
        {
            if (lblOpponentStatus.InvokeRequired)
            {
                lblOpponentStatus.Invoke(new Action(() => UpdateOpponentStatus(text, color)));
            }
            else
            {
                lblOpponentStatus.Text = text;
                lblOpponentStatus.BackColor = color;
            }
        }

        private void UpdateResult(string result, Color color)
        {
            if (lblResult.InvokeRequired)
            {
                lblResult.Invoke(new Action(() => UpdateResult(result, color)));
            }
            else
            {
                lblResult.Text = result;
                lblResult.BackColor = color;
            }
        }

        private void LogMessage(string message)
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

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            DisconnectFromServer();
            base.OnFormClosing(e);
        }
    }

    static class Client
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new ClientForm());
        }
    }
}