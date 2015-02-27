using System;
using Gtk;

namespace RPiPlotter
{
	public partial class MainWindow : Gtk.Window
	{
		ListStore commandListStore;
		Connector connector;

		public MainWindow() :
			base (WindowType.Toplevel)
		{
			this.Build ();
			this.SetupCommandTreeView ();
		}

		void SetupCommandTreeView()
		{
			commandListStore = new ListStore (typeof(Gdk.Pixbuf), typeof(string), typeof(string));
			commandTreeView.Model = commandListStore;

			// Add the columns to the TreeView
			commandTreeView.AppendColumn ("Status", new CellRendererPixbuf (), "pixbuf", 0);
			commandTreeView.AppendColumn ("Command", new CellRendererText (), "text", 1);
			commandTreeView.AppendColumn ("Time", new CellRendererText (), "text", 2);
		}

		void OnQuit(object o, EventArgs args)
		{
			if (connector != null)
				connector.Disconnect ();
			Application.Quit ();
		}

		void OnConnectActionActivated(object sender, EventArgs e)
		{
			ConnectDialog connectDialog = new ConnectDialog (this);
			connectDialog.Response += (o, args) => {
				connectDialog.Destroy ();
				if (args.ResponseId != ResponseType.Ok)
					return;
				if (connector != null)
					connector.Disconnect ();
				connector = new Connector (this, connectDialog.Hostname, connectDialog.Port);
				connector.Connected += OnConnectorConnected;
				connector.ConnectionError += OnConnectorConnectionError;
				connector.Disconnected += OnConnectorDisconnected;
				connector.CommandDone += HandleCommandDone;
				connector.CommandFail += HandleCommandFail;
				try {
					connector.Connect ();
				} catch (Exception ex) {
					var dialog = new Gtk.MessageDialog (this,
						             Gtk.DialogFlags.DestroyWithParent,
						             Gtk.MessageType.Error,
						             Gtk.ButtonsType.Ok,
						             ex.Message);
					dialog.Run ();
					dialog.Destroy ();
				}

			};
			connectDialog.Run ();
		}


		void OnConnectorConnected(object sender, EventArgs e)
		{
			disconnectAction.Sensitive = true;
			contentvbox.Sensitive = true;
		}

		void OnConnectorConnectionError(object sender, UnhandledExceptionEventArgs e)
		{
			disconnectAction.Sensitive = false;
			contentvbox.Sensitive = false;
			var dialog = new Gtk.MessageDialog (this,
				             Gtk.DialogFlags.DestroyWithParent,
				             Gtk.MessageType.Error,
				             Gtk.ButtonsType.Ok,
				             "Connection failed! " + ((Exception)e.ExceptionObject).Message);
			dialog.Run ();
			dialog.Destroy ();
		}

		void OnConnectorDisconnected(object sender, EventArgs e)
		{
			disconnectAction.Sensitive = false;
			contentvbox.Sensitive = false;
		}

		protected void OnDisconnectActionActivated(object sender, EventArgs e)
		{
			connector.Disconnect ();
		}

		void SendCommand()
		{
			if (string.IsNullOrWhiteSpace (commandEntry.Text))
				return;
			var command = commandEntry.Text.Trim ();
			connector.Send (command);
			commandEntry.Text = "";
			var iconTheme = new IconTheme ();
			var pixbuf = iconTheme.LoadIcon ("gtk-no", 16, IconLookupFlags.NoSvg);
			var iter = commandListStore.AppendValues (pixbuf, command);
			commandTreeView.ScrollToCell (commandListStore.GetPath (iter), commandTreeView.Columns [0], true, 0, 0);
		}

		protected void OnSendcommandButtonClicked(object sender, EventArgs e)
		{
			SendCommand ();

		}

		protected void OnCommandEntryActivated(object sender, EventArgs e)
		{
			SendCommand ();
		}

		void HandleCommandFail(object sender, CommandEventArgs e)
		{
			if (!string.IsNullOrEmpty (e.Message)) {
				var dialog = new Gtk.MessageDialog (this,
					             Gtk.DialogFlags.DestroyWithParent, 
					             Gtk.MessageType.Warning, 
					             Gtk.ButtonsType.Ok,
					             "Server: " + e.Message);
				dialog.Run ();
				dialog.Destroy ();
			}
		}

		void HandleCommandDone(object sender, CommandDoneEventArgs e)
		{
			if (!string.IsNullOrEmpty (e.Message)) {
				var dialog = new Gtk.MessageDialog (this,
					             Gtk.DialogFlags.DestroyWithParent, 
					             Gtk.MessageType.Info, 
					             Gtk.ButtonsType.Ok,
					             "Server: " + e.Message);
				dialog.Run ();
				dialog.Destroy ();
			}
			var count = 0;
			var lastIndex = 0;
			foreach (object[] row in commandListStore) {
				if (row [1] == e.Command)
					lastIndex = count;
				count++;
			}

		}
	}
}

