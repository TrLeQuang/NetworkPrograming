using System;

namespace RockPaperScissorsServer.Protocol
{
    public static class ProtocolMessage
    {
        // Client to Server
        public const string PLAY = "PLAY";

        // Server to Client
        public const string PLAYER_COUNT = "PLAYER_COUNT";
        public const string OPPONENT_STATUS = "OPPONENT_STATUS";
        public const string WAITING = "WAITING";
        public const string RESULT = "RESULT";

        // Opponent Status Values
        public const string STATUS_PAIRED = "PAIRED";
        public const string STATUS_DISCONNECTED = "DISCONNECTED";
        public const string STATUS_WAITING = "WAITING";

        // Result Values
        public const string RESULT_WIN = "WIN";
        public const string RESULT_LOSE = "LOSE";
        public const string RESULT_DRAW = "DRAW";

        // Choice Values
        public const string CHOICE_ROCK = "ROCK";
        public const string CHOICE_PAPER = "PAPER";
        public const string CHOICE_SCISSORS = "SCISSORS";

        public const char DELIMITER = '|';

        public static class Builder
        {
            public static string PlayerCount(int count)
            {
                return $"{PLAYER_COUNT}{DELIMITER}{count}";
            }

            public static string OpponentStatus(string status)
            {
                return $"{OPPONENT_STATUS}{DELIMITER}{status}";
            }

            public static string Waiting(string message)
            {
                return $"{WAITING}{DELIMITER}{message}";
            }

            public static string Result(string result, string yourChoice, string opponentChoice)
            {
                return $"{RESULT}{DELIMITER}{result}{DELIMITER}You: {yourChoice}, Opponent: {opponentChoice}";
            }

            public static string Play(string choice)
            {
                return $"{PLAY}{DELIMITER}{choice}";
            }
        }

        public static class Parser
        {
            public static string[] Parse(string message)
            {
                return message.Split(DELIMITER);
            }

            public static bool TryParsePlay(string message, out string choice)
            {
                choice = null;
                var parts = Parse(message);

                if (parts.Length >= 2 && parts[0] == PLAY)
                {
                    choice = parts[1];
                    return true;
                }

                return false;
            }
        }
    }
}
