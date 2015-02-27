using System;

namespace RPiPlotter
{
	public partial class ConnectDialog : Gtk.Dialog
	{
		public string Hostname { get; private set; }

		public int Port { get; private set; }


		public ConnectDialog(Gtk.Window parent)
			: base ("", parent, Gtk.DialogFlags.DestroyWithParent)
		{
			this.Build ();
		}

		void OnResponse(object sender, Gtk.ResponseArgs args)
		{
			Hostname = hostnameEntry.Text;
			Port = int.Parse (portEntry.Text);
		}

		protected void OnPortEntryChanged(object sender, EventArgs e)
		{
			if (portEntry.Text.Length > 0 && !char.IsDigit (portEntry.Text [portEntry.Text.Length - 1]))
				portEntry.Text = portEntry.Text.Remove (portEntry.Text.Length - 1);

		}
	}
}

