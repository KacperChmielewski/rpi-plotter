using System;

namespace RPiPlotter.Net
{
    public class CommandDoneEventArgs : CommandEventArgs
    {
        public string ExecutionTime { get; private set; }

        public CommandDoneEventArgs(string command, string executionTime, string message)
            : base(command, message)
        {
            ExecutionTime = executionTime;
        }

        public CommandDoneEventArgs(string command, string executionTime)
            : this(command, executionTime, string.Empty)
        {

        }
    }
}

