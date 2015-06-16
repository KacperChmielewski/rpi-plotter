using System;
using System.Net.Sockets;
using System.Threading;
using System.Text;

namespace RPiPlotter.Net
{
    public class CommandEventArgs : MessageEventArgs
    {
        public int CommandIndex { get; private set; }

        public CommandEventArgs(int commandIndex)
            : this(commandIndex, string.Empty)
        {
        }

        public CommandEventArgs(int commandIndex, string message)
            : base(message)
        {
            CommandIndex = commandIndex;
        }
    }
}

