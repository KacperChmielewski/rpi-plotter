using System;
using Gdk;

namespace RPiPlotter.Net
{
    public class ReportEventArgs : EventArgs
    {
        public string Coordinates
        {
            get;
            protected set;
        }

        public string Length
        {
            get;
            protected set;
        }

        public ReportEventArgs(string coordinates, string length)
        {
            Coordinates = coordinates;
            Length = length;
        }
    }
}

