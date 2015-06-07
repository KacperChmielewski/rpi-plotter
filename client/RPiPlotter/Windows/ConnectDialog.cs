using System;

namespace RPiPlotter.Windows
{
    public sealed partial class ConnectDialog : Gtk.Dialog
    {
        public string Hostname { get; private set; }

        public int Port { get; private set; }


        public ConnectDialog(Gtk.Window parent)
            : base("", parent, Gtk.DialogFlags.DestroyWithParent)
        {
            this.Build();
            hostnameEntry.GrabFocus();
        }

        void OnResponse(object sender, Gtk.ResponseArgs args)
        {
            Hostname = hostnameEntry.Text;
            Port = int.Parse(portEntry.Text);
        }

        void OnPortEntryChanged(object sender, EventArgs e)
        {
            if (portEntry.Text.Length > 0 && !char.IsDigit(portEntry.Text[portEntry.Text.Length - 1]))
                portEntry.Text = portEntry.Text.Remove(portEntry.Text.Length - 1);

        }

        void OnEntryActivated(object sender, EventArgs e)
        {
            buttonOk.Click();
        }
    }
}

