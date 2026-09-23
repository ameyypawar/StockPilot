using System;

namespace InventoryManagementSystem.Utilities
{
    // Exception/EOF handling: wraps Console.ReadLine so a closed input stream exits cleanly.
    public static class InputHelper
    {
        public static string ReadLine()
        {
            string? line = Console.ReadLine();
            if (line == null)
            {
                Console.WriteLine("No more input. Exiting.");
                Environment.Exit(0);
            }
            return line;
        }
    }
}
