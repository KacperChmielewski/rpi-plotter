using System;
using System.Net.Sockets;
using System.Threading;
using System.Text;

namespace RPiPlotter.Net
{
    public class CommandEventArgs : EventArgs
    {
        public int CommandIndex { get; private set; }

        public string Message { get; private set; }

        public CommandEventArgs(int commandIndex)
        {
            CommandIndex = commandIndex;
        }

        public CommandEventArgs(int commandIndex, string message)
            : this(commandIndex)
        {
            Message = message;
        }
    }
}

