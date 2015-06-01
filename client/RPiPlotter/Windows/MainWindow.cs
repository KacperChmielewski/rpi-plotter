using System;
using Gtk;

namespace RPiPlotter
{
	public partial class MainWindow : Gtk.Window
	{
		ListStore commandListStore;
		Connector connector;
		Gdk.Pixbuf donePixbuf, errorPixbuf, executingPixbuf;
		string commands = "";

		public MainWindow () :
			base (WindowType.Toplevel)
		{
			this.Build ();
			this.SetupCommandTreeView ();
			this.LoadIcons ();
		}

		void SetupCommandTreeView ()
		{
			commandListStore = new ListStore (typeof(Gdk.Pixbuf), typeof(string), typeof(string), typeof(bool));
			commandTreeView.Model = commandListStore;

			// Add the columns to the TreeView
			commandTreeView.AppendColumn ("Status", new CellRendererPixbuf (), "pixbuf", 0);
			commandTreeView.AppendColumn ("Command", new CellRendererText (), "text", 1);
			commandTreeView.AppendColumn ("Time", new CellRendererText (), "text", 2);
		}

		void LoadIcons ()
		{
			var iconTheme = new IconTheme ();

			donePixbuf = iconTheme.LoadIcon ("gtk-apply", 16, IconLookupFlags.NoSvg);
			errorPixbuf = new Gdk.Pixbuf ("Icons/error.png");
			executingPixbuf = new Gdk.Pixbuf ("Icons/execute.png");
		}

		void OnQuit (object o, EventArgs args)
		{
			if (connector != null)
				connector.Disconnect ();
			Application.Quit ();
		}

		void OnConnectActionActivated (object sender, EventArgs e)
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
				connector.CommandExecuting += HandleCommandExecuting;
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


		void OnConnectorConnected (object sender, EventArgs e)
		{
			disconnectAction.Sensitive = true;
			contentvbox.Sensitive = true;
		}

		void OnConnectorConnectionError (object sender, UnhandledExceptionEventArgs e)
		{
			DisconnectUIChange ();
			var dialog = new Gtk.MessageDialog (this,
				             Gtk.DialogFlags.DestroyWithParent,
				             Gtk.MessageType.Error,
				             Gtk.ButtonsType.Ok,
				             "Connection failed! " + ((Exception)e.ExceptionObject).Message);
			dialog.Run ();
			dialog.Destroy ();
		}

		void DisconnectUIChange ()
		{
			disconnectAction.Sensitive = false;
			contentvbox.Sensitive = false;
			commandListStore.Clear ();
		}

		void OnConnectorDisconnected (object sender, EventArgs e)
		{
			DisconnectUIChange ();
		}

		protected void OnDisconnectActionActivated (object sender, EventArgs e)
		{
			connector.Disconnect ();
		}

		void SendCommand ()
		{
			if (string.IsNullOrWhiteSpace (commandEntry.Text))
				return;
			SendCommand (commandEntry.Text);
			commandEntry.Text = "";
		}

		void SendCommand (string command)
		{
			command = command.Trim ();
			connector.Send (command);
			var iter = commandListStore.AppendValues (null, command);
			commandTreeView.ScrollToCell (commandListStore.GetPath (iter), commandTreeView.Columns [0], true, 0, 0);
		}

		protected void OnSendcommandButtonClicked (object sender, EventArgs e)
		{
			SendCommand ();
		}

		protected void OnCommandEntryActivated (object sender, EventArgs e)
		{
			SendCommand ();
		}

		protected void OnCommandTreeViewRowActivated (object o, RowActivatedArgs args)
		{
			TreeIter iter;
			commandListStore.GetIter (out iter, args.Path);
			if ((bool)commandListStore.GetValue (iter, 3) == true) {
				SendCommand ((string)commandListStore.GetValue (iter, 1));
			}

		}

		void HandleCommandFail (object sender, CommandEventArgs e)
		{
			var index = 0;
			foreach (object[] row in commandListStore) {
				if (e.Command.Equals (row [1]) && row [0] == executingPixbuf) {
					break;
				}
				index++;
			}
			TreeIter iter;
			if (commandListStore.GetIterFromString (out iter, index.ToString ())) {
				commandListStore.SetValue (iter, 0, errorPixbuf);
			}
			if (!string.IsNullOrEmpty (e.Message)) {
				var dialog = new Gtk.MessageDialog (this,
					             Gtk.DialogFlags.DestroyWithParent, 
					             Gtk.MessageType.Warning, 
					             Gtk.ButtonsType.Ok,
					             false,
					             "Server: " + e.Message);
				dialog.Run ();
				dialog.Destroy ();
			}
			index = 0;
			foreach (object[] row in commandListStore) {
				if (row [0] == null) {
					if (commandListStore.GetIterFromString (out iter, index.ToString ())) {
						commandListStore.SetValue (iter, 0, errorPixbuf);
					}
				}
				index++;
			}
		}

		void HandleCommandDone (object sender, CommandDoneEventArgs e)
		{
			var index = 0;
			foreach (object[] row in commandListStore) {
				if (e.Command.Equals (row [1]) && row [0] == executingPixbuf) {
					break;
				}
				index++;
			}
			TreeIter iter;
			if (commandListStore.GetIterFromString (out iter, index.ToString ())) {
				commandListStore.SetValue (iter, 0, donePixbuf);
				commandListStore.SetValue (iter, 2, e.ExecutionTime);
				commandListStore.SetValue (iter, 3, true);
			}
			if (!string.IsNullOrEmpty (e.Message)) {
				var dialog = new Gtk.MessageDialog (this,
					             Gtk.DialogFlags.DestroyWithParent, 
					             Gtk.MessageType.Info, 
					             Gtk.ButtonsType.Ok,
					             "Server: " + e.Message);
				dialog.Run ();
				dialog.Destroy ();
			}
		}

		void HandleCommandExecuting (object sender, CommandEventArgs e)
		{
			var index = 0;
			foreach (object[] row in commandListStore) {
				if (e.Command.Equals (row [1]) && row [0] == null) {
					break;
				}
				index++;
			}
			TreeIter iter;
			if (commandListStore.GetIterFromString (out iter, index.ToString ())) {
				commandListStore.SetValue (iter, 0, executingPixbuf);
			}
		}

		protected void OnPreviewActionActivated (object sender, EventArgs e)
		{
			var action = sender as ToggleAction;
			if (action.Active) {
				// TODO: enable preview
			} else {
				// TODO: disable preview
			}
		}
	}
}

