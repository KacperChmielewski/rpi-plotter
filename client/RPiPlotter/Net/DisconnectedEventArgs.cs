using System;

namespace RPiPlotter.Net
{
    public class DisconnectedEventArgs : EventArgs
    {
        public bool ServerDisconnect { get; protected set; }

        public DisconnectedEventArgs(bool serverDisconnect)
        {
            ServerDisconnect = serverDisconnect;
        }
    }
}

