using System;

namespace RPiPlotter.Net
{
    public class ProgressEventArgs : EventArgs
    {
        public int Current { get; private set; }

        public int Total { get; private set; }

        public ProgressEventArgs(int current, int total)
        {
            Current = current;
            Total = total;
        }
    }
}

