using System;

namespace RockPaperScissorsClient.Game
{
    public class GameState
    {
        public bool IsConnected { get; set; }
        public int PlayersOnline { get; set; }
        public bool HasOpponent { get; set; }
        public string LastChoice { get; set; }
        public string LastResult { get; set; }
        public string LastOpponentChoice { get; set; }
        public bool IsWaitingForOpponent { get; set; }

        public GameState()
        {
            Reset();
        }

        public void Reset()
        {
            IsConnected = false;
            PlayersOnline = 0;
            HasOpponent = false;
            LastChoice = null;
            LastResult = null;
            LastOpponentChoice = null;
            IsWaitingForOpponent = false;
        }

        public void OnConnected()
        {
            IsConnected = true;
        }

        public void OnDisconnected()
        {
            Reset();
        }

        public void OnPlayerCountUpdate(int count)
        {
            PlayersOnline = count;
        }

        public void OnOpponentPaired()
        {
            HasOpponent = true;
            IsWaitingForOpponent = false;
        }

        public void OnOpponentDisconnected()
        {
            HasOpponent = false;
            IsWaitingForOpponent = false;
        }

        public void OnChoiceMade(string choice)
        {
            LastChoice = choice;
            IsWaitingForOpponent = true;
        }

        public void OnResultReceived(string result, string yourChoice, string opponentChoice)
        {
            LastResult = result;
            LastChoice = yourChoice;
            LastOpponentChoice = opponentChoice;
            IsWaitingForOpponent = false;
        }
    }
}