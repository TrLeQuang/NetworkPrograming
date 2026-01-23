using RockPaperScissorsServer.Protocol;

namespace RockPaperScissorsServer.Game
{
    public static class GameLogic
    {
        public static string DetermineWinner(string choice1, string choice2)
        {
            if (choice1 == choice2)
            {
                return ProtocolMessage.RESULT_DRAW;
            }

            if (IsWinningCombination(choice1, choice2))
            {
                return ProtocolMessage.RESULT_WIN;
            }

            return ProtocolMessage.RESULT_LOSE;
        }

        public static string GetOppositeResult(string result)
        {
            if (result == ProtocolMessage.RESULT_WIN)
            {
                return ProtocolMessage.RESULT_LOSE;
            }

            if (result == ProtocolMessage.RESULT_LOSE)
            {
                return ProtocolMessage.RESULT_WIN;
            }

            return ProtocolMessage.RESULT_DRAW;
        }

        private static bool IsWinningCombination(string choice1, string choice2)
        {
            return (choice1 == ProtocolMessage.CHOICE_ROCK && choice2 == ProtocolMessage.CHOICE_SCISSORS) ||
                   (choice1 == ProtocolMessage.CHOICE_PAPER && choice2 == ProtocolMessage.CHOICE_ROCK) ||
                   (choice1 == ProtocolMessage.CHOICE_SCISSORS && choice2 == ProtocolMessage.CHOICE_PAPER);
        }

        public static bool IsValidChoice(string choice)
        {
            return choice == ProtocolMessage.CHOICE_ROCK ||
                   choice == ProtocolMessage.CHOICE_PAPER ||
                   choice == ProtocolMessage.CHOICE_SCISSORS;
        }
    }
}