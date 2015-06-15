using System;
using Gtk;
using System.Text.RegularExpressions;
using RPiPlotter.Net;
using System.Linq;

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
            var filter = new FileFilter();
            filter.Name = "Plotter path file";
            filter.AddPattern("*.plo");
            fileChooserButton.Filter = filter;
            this.SetupCommandTreeView();
            this.LoadIcons();
            //var configuration = System.Configuration.ConfigurationManager.OpenExeConfiguration(System.Configuration.ConfigurationUserLevel.None);

        }

        void SetupCommandTreeView()
        {
            commandListStore = new ListStore(typeof(int), typeof(Gdk.Pixbuf), typeof(string), typeof(string));
            commandTreeView.Model = commandListStore;
            var wrapCell = new CellRendererText()
            {
                WrapMode = Pango.WrapMode.Word
            };

            // Add the columns to the TreeView
            commandTreeView.AppendColumn("Status", new CellRendererPixbuf(), "pixbuf", 1);
            commandTreeView.AppendColumn("Command", wrapCell, "text", 2);
            commandTreeView.AppendColumn("Time", new CellRendererText(), "text", 3);
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
            int index = connector.Send(command);
            if (index != -1)
            {
                var iter = commandListStore.AppendValues(index, null, command);
                commandTreeView.ScrollToCell(commandListStore.GetPath(iter), commandTreeView.Columns[0], true, 0, 0);
            }

        }

        void ConnectUIChange()
        {
            disconnectAction.Sensitive = true;
            commandvbox.Sensitive = true;
            filevbox.Sensitive = true;
            sendcommandButton.Sensitive = false;
            connectStatusLabel.Text = "Connected to " + connector.Hostname;
            connectStatusImage.Pixbuf = connectedPixbuf;
            PauseExecutionAction.Sensitive = true;
            ServerInfoAction.Sensitive = true;
            GetStateInfoAction.Sensitive = true;
        }

        void DisconnectUIChange()
        {
            disconnectAction.Sensitive = false;
            commandvbox.Sensitive = false;
            filevbox.Sensitive = false;
            PauseExecutionAction.Sensitive = false;
            ServerInfoAction.Sensitive = false;
            connectStatusLabel.Text = "Disconnected";
            connectStatusImage.Pixbuf = disconnectedPixbuf;
            commandListStore.Clear();
            previewWindow.ClearPaths();
        }

        void FileStartUIChange()
        {
            fileProgressFrame.Visible = true;
            CommandModeAction.Sensitive = false;
            fileProgressBar.Text = "Sending file...";
            filechooserhbox.Sensitive = false;
        }

        void FileEndUIChange()
        {
            cancelFileButton.Sensitive = false;
            fileProgressFrame.Visible = false;
            CommandModeAction.Sensitive = true;
            filechooserhbox.Sensitive = true;
            fileProgressBar.Fraction = 0;
            fileProgressBar.Text = "";
            fileChooserButton.UnselectAll();
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
                connector.FileCompleted += HandleFileCompleted;
                connector.FileError += HandleFileError;
                connector.FileProgress += HandleFileProgress;
                connector.FileSended += HandleFileSended;

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
            ConnectUIChange();
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

        #endregion

        #region Connector Command Events

        void HandleCommandFail(object sender, CommandEventArgs e)
        {
            var index = 0;
            foreach (object[] row in commandListStore)
            {
                if (e.CommandIndex.Equals(row[0]) && row[1] == executingPixbuf)
                {
                    break;
                }
                index++;
            }
            TreeIter iter;
            if (commandListStore.GetIterFromString(out iter, index.ToString()))
            {
                commandListStore.SetValue(iter, 1, errorPixbuf);

                if (previewWindow != null)
                    previewWindow.ExecutingPathData = "";
            }
            commandListStore.GetIterFirst(out iter);
            do
            {
                if (commandListStore.GetValue(iter, 1) == null)
                {
                    commandListStore.SetValue(iter, 1, errorPixbuf);
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
                if (e.CommandIndex.Equals(row[0]) && row[1] == executingPixbuf)
                {
                    break;
                }
                index++;
            }
            TreeIter iter;
            if (commandListStore.GetIterFromString(out iter, index.ToString()))
            {
                commandListStore.SetValue(iter, 1, donePixbuf);
                commandListStore.SetValue(iter, 3, e.ExecutionTime);

                if (previewWindow != null)
                {
                    string command = commandListStore.GetValue(iter, 2) as string;
                    Regex.Replace(command, @"\s*[A-Za-z]{2,}\s*[\d\W]*", "");
                    previewWindow.PathData += " " + command;
                }
            }

            bool allDone = true;
            foreach (object[] row in commandListStore)
            {
                if (row[1] == executingPixbuf)
                    allDone = false;
            }
            FileModeAction.Sensitive = allDone;

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
            FileModeAction.Sensitive = false;
            var index = 0;
            foreach (object[] row in commandListStore)
            {
                if (e.CommandIndex.Equals(row[0]) && row[1] == null)
                {
                    break;
                }
                index++;
            }
            TreeIter iter;
            if (commandListStore.GetIterFromString(out iter, index.ToString()))
            {
                commandListStore.SetValue(iter, 1, executingPixbuf);

                if (previewWindow != null)
                {
                    string command = commandListStore.GetValue(iter, 2) as string;
                    Regex.Replace(command, @"\s*[A-Za-z]{2,}\s*[\d\W]*", "");
                    previewWindow.ExecutingPathData = command;
                }

            }
        }

        void HandleMessageReceived(object sender, MessageEventArgs e)
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

        #region Connector File Events

        void HandleFileCompleted(object sender, EventArgs e)
        {
            FileEndUIChange();
        }

        void HandleFileError(object sender, MessageEventArgs e)
        {
            FileEndUIChange();
            if (e.Message != string.Empty)
            {
                var dialog = new Gtk.MessageDialog(this,
                                 Gtk.DialogFlags.DestroyWithParent, 
                                 Gtk.MessageType.Error, 
                                 Gtk.ButtonsType.Ok,
                                 true,
                                 "File execution failed: " + e.Message);
                dialog.Run();
                dialog.Destroy();
            }
        }

        void HandleFileProgress(object sender, ProgressEventArgs e)
        {
            fileProgressBar.Fraction = (float)e.Current / e.Total;
            fileProgressBar.Text = string.Format("Executing ({0}/{1})", e.Current, e.Total);
        }

        void HandleFileSended(object sender, EventArgs e)
        {
            fileProgressFrameLabel.Text = fileChooserButton.Filename;
            fileProgressBar.Text = "Executing...";
            cancelFileButton.Sensitive = true;
        }

        #endregion

        void OnCommandTreeViewRowActivated(object o, RowActivatedArgs args)
        {
            TreeIter iter;
            commandListStore.GetIter(out iter, args.Path);
            if (commandListStore.GetValue(iter, 1) == donePixbuf)
            {
                SendCommand((string)commandListStore.GetValue(iter, 2));
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
            sendcommandButton.Sensitive = !string.IsNullOrWhiteSpace(text) && Regex.IsMatch(text, @"^\s*[A-Za-z].*");
        }

        void OnSendcommandButtonClicked(object sender, EventArgs e)
        {
            SendCommand();
        }

        void OnPanicButtonClicked(object sender, EventArgs e)
        {
            connector.SendServerCommand("PANIC");
        }

        void OnDisconnectActionActivated(object sender, EventArgs e)
        {
            connector.Disconnect();
        }

        void OnCommandEntryActivated(object sender, EventArgs e)
        {
            if (sendcommandButton.Sensitive)
                SendCommand();
        }

        void OnPauseExecutionActionToggled(object sender, EventArgs e)
        {
            if (PauseExecutionAction.Active)
                connector.SendServerCommand("PAUSE");
            else
                connector.SendServerCommand("UNPAUSE");
        }

        void OnServerInfoActionActivated(object sender, EventArgs e)
        {
            connector.SendServerCommand("INFO");
        }

        protected void OnGetStateInfoActionActivated(object sender, EventArgs e)
        {
            connector.SendServerCommand("STATE");
        }

        void OnCommandModeActionToggled(object sender, EventArgs e)
        {
            notebook.Page = 0;
        }

        void OnFileModeActionToggled(object sender, EventArgs e)
        {
            notebook.Page = 1;
        }

        void OnFileSendButtonClicked(object sender, EventArgs e)
        {
            FileStartUIChange();
            connector.SendFile(fileChooserButton.Filename);
        }

        void OnCancelFileButtonClicked(object sender, EventArgs e)
        {
            connector.SendServerCommand("PANIC");
        }

        void OnFileChooserButtonSelectionChanged(object sender, EventArgs e)
        {
            fileSendButton.Sensitive = fileChooserButton.Filename != null;
        }
    }
}

