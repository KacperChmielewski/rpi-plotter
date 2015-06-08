using System;

namespace RPiPlotter.Net
{
    public class CommandDoneEventArgs : CommandEventArgs
    {
        public string ExecutionTime { get; private set; }

        public CommandDoneEventArgs(int commandIndex, string executionTime, string message)
            : base(commandIndex, message)
        {
            ExecutionTime = executionTime;
        }

        public CommandDoneEventArgs(int commandIndex, string executionTime)
            : this(commandIndex, executionTime, string.Empty)
        {

        }
    }
}

