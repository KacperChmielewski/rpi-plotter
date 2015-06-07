using System;
using Gtk;
using System.Text.RegularExpressions;
using RPiPlotter.Net;

namespace RPiPlotter.Windows
{
    public sealed partial class MainWindow : Gtk.Window
    {
        ListStore commandListStore;
        Connector connector;
        Gdk.Pixbuf donePixbuf, errorPixbuf, executingPixbuf, connectedPixbuf, disconnectedPixbuf;
        PreviewWindow previewWindow;

        public MainWindow()
            : base(WindowType.Toplevel)
        {
            this.Build();
            previewWindow = new PreviewWindow();
            previewWindow.Hidden += (o, args) => PreviewAction.Active = false;
            previewWindow.Hide();
            this.SetupCommandTreeView();
            this.LoadIcons();
        }

        void SetupCommandTreeView()
        {
            commandListStore = new ListStore(typeof(Gdk.Pixbuf), typeof(string), typeof(string), typeof(bool));
            commandTreeView.Model = commandListStore;

            // Add the columns to the TreeView
            commandTreeView.AppendColumn("Status", new CellRendererPixbuf(), "pixbuf", 0);
            commandTreeView.AppendColumn("Command", new CellRendererText(), "text", 1);
            commandTreeView.AppendColumn("Time", new CellRendererText(), "text", 2);
        }

        void LoadIcons()
        {
            var iconTheme = new IconTheme();

            donePixbuf = iconTheme.LoadIcon("gtk-apply", 16, IconLookupFlags.NoSvg);
            errorPixbuf = new Gdk.Pixbuf("Icons/error.png");
            executingPixbuf = new Gdk.Pixbuf("Icons/execute.png");
            connectedPixbuf = iconTheme.LoadIcon("gtk-connect", 16, IconLookupFlags.NoSvg);
            disconnectedPixbuf = iconTheme.LoadIcon("gtk-disconnect", 16, IconLookupFlags.NoSvg);
        }

        void SendCommand()
        {
            if (string.IsNullOrWhiteSpace(commandEntry.Text))
                return;
            SendCommand(commandEntry.Text);
            commandEntry.Text = "";
        }

        void SendCommand(string command)
        {
            command = command.Trim();
            connector.Send(command);
            var iter = commandListStore.AppendValues(null, command);
            commandTreeView.ScrollToCell(commandListStore.GetPath(iter), commandTreeView.Columns[0], true, 0, 0);
        }

        void DisconnectUIChange()
        {
            disconnectAction.Sensitive = false;
            contentvbox.Sensitive = false;
            PauseExecutionAction.Sensitive = false;
            ServerInfoAction.Sensitive = false;
            connectStatusLabel.Text = "Disconnected";
            connectStatusImage.Pixbuf = disconnectedPixbuf;
            commandListStore.Clear();
            previewWindow.ClearPaths();
        }

        void OnQuit(object o, EventArgs args)
        {
            if (connector != null)
                connector.Disconnect();
            Application.Quit();
        }

        void OnConnectActionActivated(object sender, EventArgs e)
        {
            ConnectDialog connectDialog = new ConnectDialog(this);
            connectDialog.Response += (o, args) =>
            {
                connectDialog.Destroy();
                if (args.ResponseId != ResponseType.Ok)
                    return;
                if (connector != null && connector.IsConnected)
                    connector.Disconnect();
                connector = new Connector(this, connectDialog.Hostname, connectDialog.Port);
                connector.Connected += OnConnectorConnected;
                connector.ConnectionError += OnConnectorConnectionError;
                connector.Disconnected += OnConnectorDisconnected;
                connector.CommandDone += HandleCommandDone;
                connector.CommandFail += HandleCommandFail;
                connector.CommandExecuting += HandleCommandExecuting;
                connector.MessageReceived += HandleMessageReceived;
                try
                {
                    connector.Connect();
                }
                catch (Exception ex)
                {
                    var dialog = new Gtk.MessageDialog(this,
                                     Gtk.DialogFlags.DestroyWithParent,
                                     Gtk.MessageType.Error,
                                     Gtk.ButtonsType.Ok,
                                     ex.Message);
                    dialog.Run();
                    dialog.Destroy();
                }

            };
            connectDialog.Run();
        }

        #region Connector Events

        void OnConnectorConnected(object sender, EventArgs e)
        {
            disconnectAction.Sensitive = true;
            contentvbox.Sensitive = true;
            sendcommandButton.Sensitive = false;
            connectStatusLabel.Text = "Connected to " + connector.Hostname;
            connectStatusImage.Pixbuf = connectedPixbuf;
            PauseExecutionAction.Sensitive = true;
            ServerInfoAction.Sensitive = true;
            GetStateInfoAction.Sensitive = true;
        }

        void OnConnectorConnectionError(object sender, UnhandledExceptionEventArgs e)
        {
            DisconnectUIChange();
            var dialog = new Gtk.MessageDialog(this,
                             Gtk.DialogFlags.DestroyWithParent,
                             Gtk.MessageType.Error,
                             Gtk.ButtonsType.Ok,
                             "Connection failed! " + ((Exception)e.ExceptionObject).Message);
            dialog.Run();
            dialog.Destroy();
        }

        void OnConnectorDisconnected(object sender, DisconnectedEventArgs e)
        {
            DisconnectUIChange();
            if (e.ServerDisconnect)
            {
                var dialog = new Gtk.MessageDialog(this,
                                 Gtk.DialogFlags.DestroyWithParent,
                                 Gtk.MessageType.Error,
                                 Gtk.ButtonsType.Ok,
                                 "Disconnected from server!");
                dialog.Run();
                dialog.Destroy();
            }
        }

        void OnDisconnectActionActivated(object sender, EventArgs e)
        {
            connector.Disconnect();
        }

        void HandleCommandFail(object sender, CommandEventArgs e)
        {
            var index = 0;
            foreach (object[] row in commandListStore)
            {
                if (e.Command.Equals(row[1]) && row[0] == executingPixbuf)
                {
                    break;
                }
                index++;
            }
            TreeIter iter;
            if (commandListStore.GetIterFromString(out iter, index.ToString()))
            {
                commandListStore.SetValue(iter, 0, errorPixbuf);

                if (previewWindow != null)
                    previewWindow.ExecutingPathData = "";
            }
            commandListStore.GetIterFirst(out iter);
            do
            {
                if (commandListStore.GetValue(iter, 0) == null)
                {
                    commandListStore.SetValue(iter, 0, errorPixbuf);
                }
            }
            while (commandListStore.IterNext(ref iter));
            if (!string.IsNullOrEmpty(e.Message))
            {
                var dialog = new Gtk.MessageDialog(this,
                                 Gtk.DialogFlags.DestroyWithParent, 
                                 Gtk.MessageType.Warning, 
                                 Gtk.ButtonsType.Ok,
                                 false,
                                 "Server: " + e.Message);
                dialog.Run();
                dialog.Destroy();
            }
        }

        void HandleCommandDone(object sender, CommandDoneEventArgs e)
        {
            var index = 0;
            foreach (object[] row in commandListStore)
            {
                if (e.Command.Equals(row[1]) && row[0] == executingPixbuf)
                {
                    break;
                }
                index++;
            }
            TreeIter iter;
            if (commandListStore.GetIterFromString(out iter, index.ToString()))
            {
                commandListStore.SetValue(iter, 0, donePixbuf);
                commandListStore.SetValue(iter, 2, e.ExecutionTime);
                commandListStore.SetValue(iter, 3, true);

                if (previewWindow != null)
                {
                    string command = commandListStore.GetValue(iter, 1) as string;
                    Regex.Replace(command, @"\s*[A-Za-z]{2,}\s*[\d\W]*", "");
                    previewWindow.PathData += " " + command;
                }
            }
            if (!string.IsNullOrEmpty(e.Message))
            {
                var dialog = new Gtk.MessageDialog(this,
                                 Gtk.DialogFlags.DestroyWithParent, 
                                 Gtk.MessageType.Info, 
                                 Gtk.ButtonsType.Ok,
                                 "Server: " + e.Message);
                dialog.Run();
                dialog.Destroy();
            }
        }

        void HandleCommandExecuting(object sender, CommandEventArgs e)
        {
            var index = 0;
            foreach (object[] row in commandListStore)
            {
                if (e.Command.Equals(row[1]) && row[0] == null)
                {
                    break;
                }
                index++;
            }
            TreeIter iter;
            if (commandListStore.GetIterFromString(out iter, index.ToString()))
            {
                commandListStore.SetValue(iter, 0, executingPixbuf);

                if (previewWindow != null)
                {
                    string command = commandListStore.GetValue(iter, 1) as string;
                    Regex.Replace(command, @"\s*[A-Za-z]{2,}\s*[\d\W]*", "");
                    previewWindow.ExecutingPathData = command;
                }

            }
        }

        void HandleMessageReceived(object sender, MessageReceivedEventArgs e)
        {
            if (!string.IsNullOrEmpty(e.Message))
            {
                var dialog = new Gtk.MessageDialog(this,
                                 Gtk.DialogFlags.DestroyWithParent, 
                                 Gtk.MessageType.Info, 
                                 Gtk.ButtonsType.Ok,
                                 true,
                                 e.Message);
                dialog.Run();
                dialog.Destroy();
            }
        }

        #endregion

        void OnCommandTreeViewRowActivated(object o, RowActivatedArgs args)
        {
            TreeIter iter;
            commandListStore.GetIter(out iter, args.Path);
            if ((bool)commandListStore.GetValue(iter, 3) == true)
            {
                SendCommand((string)commandListStore.GetValue(iter, 1));
            }

        }


        void OnPreviewActionToggled(object sender, EventArgs e)
        {
            var action = sender as ToggleAction;
            if (action.Active)
            {
                previewWindow.Show();
            }
            else
            {
                previewWindow.Hide();
            }
        }

        void OnCommandEntryChanged(object sender, EventArgs e)
        {
            var text = commandEntry.Text;
            if (!string.IsNullOrWhiteSpace(text) && Regex.IsMatch(text, @"^\s*[A-Za-z].*"))
            {
                sendcommandButton.Sensitive = true;
            }
            else
            {
                sendcommandButton.Sensitive = false;
            }
        }

        void OnSendcommandButtonClicked(object sender, EventArgs e)
        {
            SendCommand();
        }

        void OnPanicButtonClicked(object sender, EventArgs e)
        {
            connector.Send("!PANIC");
        }

        void OnCommandEntryActivated(object sender, EventArgs e)
        {
            if (sendcommandButton.Sensitive)
                SendCommand();
        }

        void OnPauseExecutionActionToggled(object sender, EventArgs e)
        {
            if (PauseExecutionAction.Active)
                connector.Send("!PAUSE");
            else
                connector.Send("!UNPAUSE");
        }

        void OnServerInfoActionActivated(object sender, EventArgs e)
        {
            connector.Send("!INFO");
        }
    }
}

