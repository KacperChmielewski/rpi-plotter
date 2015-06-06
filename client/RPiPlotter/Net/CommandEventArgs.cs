using System;
using System.Net.Sockets;
using System.Threading;
using System.Text;

namespace RPiPlotter.Net
{
    public class CommandEventArgs : EventArgs
    {
        public string Command { get; private set; }

        public string Message { get; private set; }

        public CommandEventArgs(string command)
        {
            Command = command;
        }

        public CommandEventArgs(string command, string message)
            : this(command)
        {
            Message = message;
        }
    }
}

