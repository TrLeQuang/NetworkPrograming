using System.Collections.Generic;
using System.Linq;
using RockPaperScissorsServer.Network;
using RockPaperScissorsServer.Protocol;

namespace RockPaperScissorsServer.Matchmaking
{
    public class Matchmaker
    {
        private List<GamePair> gamePairs = new List<GamePair>();

        public int PairCount => gamePairs.Count;

        public bool TryPairClient(ClientHandler newClient, List<ClientHandler> allClients)
        {
            // Tìm client đang chờ ghép cặp (chưa có partner)
            var waitingClient = allClients.FirstOrDefault(c => c != newClient && c.Partner == null);

            if (waitingClient != null)
            {
                // Ghép cặp hai client
                GamePair pair = new GamePair(waitingClient, newClient);
                gamePairs.Add(pair);

                waitingClient.Partner = newClient;
                newClient.Partner = waitingClient;

                waitingClient.SendMessage(ProtocolMessage.Builder.OpponentStatus(ProtocolMessage.STATUS_PAIRED));
                newClient.SendMessage(ProtocolMessage.Builder.OpponentStatus(ProtocolMessage.STATUS_PAIRED));

                return true;
            }

            // Không có ai chờ, client này sẽ chờ người tiếp theo
            newClient.SendMessage(ProtocolMessage.Builder.Waiting("Waiting for another player to join..."));
            return false;
        }

        public void RemovePair(ClientHandler client)
        {
            var pair = gamePairs.FirstOrDefault(p => p.Player1 == client || p.Player2 == client);

            if (pair != null)
            {
                gamePairs.Remove(pair);

                // Thông báo cho partner rằng đối thủ đã disconnect
                var partner = client.Partner;
                if (partner != null)
                {
                    partner.Partner = null;
                    partner.SendMessage(ProtocolMessage.Builder.OpponentStatus(ProtocolMessage.STATUS_DISCONNECTED));
                }
            }
        }

        public void Clear()
        {
            gamePairs.Clear();
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
}