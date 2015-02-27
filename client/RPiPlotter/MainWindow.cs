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
			TreeViewColumn statusColumn = new TreeViewColumn ();
			statusColumn.Title = "Status";

			TreeViewColumn commandColumn = new TreeViewColumn ();
			commandColumn.Title = "Command";

			// Add the columns to the TreeView
			commandTreeView.AppendColumn (statusColumn);
			commandTreeView.AppendColumn (commandColumn);

			commandListStore = new ListStore (typeof(Image), typeof(string));
			commandTreeView.Model = commandListStore;
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
				if (args.ResponseId != ResponseType.Ok)
					return;
				connector = new Connector (this, connectDialog.Hostname, connectDialog.Port);
				connector.Connected += OnConnectorConnected;
				connector.ConnectionError += OnConnectorConnectionError;
				try {
					connector.Connect ();
				} catch (Exception ex) {
					var dialog = new Gtk.MessageDialog (this,
						Gtk.DialogFlags.DestroyWithParent,
						Gtk.MessageType.Error,
						Gtk.ButtonsType.Ok,
						"Connecting failed! " + ex.Message);
					dialog.Run ();
					dialog.Destroy ();
				}

			};
			connectDialog.Run ();
			connectDialog.Destroy ();
		}

		void OnConnectorConnected(object sender, EventArgs e)
		{
			disconnectAction.Sensitive = true;
			contentvbox.Sensitive = true;
		}

		void OnConnectorConnectionError(object sender, UnhandledExceptionEventArgs e)
		{
			if (e.IsTerminating) {
				disconnectAction.Sensitive = false;
				contentvbox.Sensitive = false;
			}
			var dialog = new Gtk.MessageDialog (this,
				             Gtk.DialogFlags.DestroyWithParent,
				             Gtk.MessageType.Error,
				             Gtk.ButtonsType.Ok,
				             "Connection failed! " + ((Exception)e.ExceptionObject).Message);
			dialog.Run ();
			dialog.Destroy ();
		}
	}
}

