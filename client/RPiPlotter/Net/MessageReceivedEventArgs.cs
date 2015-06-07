using System;

namespace RPiPlotter.Net
{
    public class MessageReceivedEventArgs
    {
        public string Message
        {
            get;
            private set;
        }

        public MessageReceivedEventArgs(string message)
        {
            Message = message;
        }
    }
}

