using System;

namespace RPiPlotter.Net
{
    public class MessageEventArgs
    {
        public string Message
        {
            get;
            protected set;
        }

        public MessageEventArgs(string message)
        {
            Message = message;
        }
    }
}

