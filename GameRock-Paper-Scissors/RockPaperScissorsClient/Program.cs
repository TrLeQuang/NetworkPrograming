using System;
using System.Windows.Forms;
using RockPaperScissorsClient.UI;

namespace RockPaperScissorsClient
{
    static class Program
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