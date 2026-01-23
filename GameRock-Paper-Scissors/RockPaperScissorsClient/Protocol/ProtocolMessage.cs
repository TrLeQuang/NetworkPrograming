using System;

namespace RockPaperScissorsClient.Protocol
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

            public static bool TryParsePlayerCount(string message, out int count)
            {
                count = 0;
                var parts = Parse(message);

                if (parts.Length >= 2 && parts[0] == PLAYER_COUNT)
                {
                    return int.TryParse(parts[1], out count);
                }

                return false;
            }

            public static bool TryParseOpponentStatus(string message, out string status)
            {
                status = null;
                var parts = Parse(message);

                if (parts.Length >= 2 && parts[0] == OPPONENT_STATUS)
                {
                    status = parts[1];
                    return true;
                }

                return false;
            }

            public static bool TryParseWaiting(string message, out string waitMessage)
            {
                waitMessage = null;
                var parts = Parse(message);

                if (parts.Length >= 2 && parts[0] == WAITING)
                {
                    waitMessage = parts[1];
                    return true;
                }

                return false;
            }

            public static bool TryParseResult(string message, out string result, out string details)
            {
                result = null;
                details = null;
                var parts = Parse(message);

                if (parts.Length >= 3 && parts[0] == RESULT)
                {
                    result = parts[1];
                    details = parts[2];
                    return true;
                }

                return false;
            }
        }
    }
}