using System;
using System.Net.Sockets;
using System.Threading;
using System.Text;

namespace RPiPlotter
{
	public delegate void CommandEventHandler (object sender, CommandEventArgs e);
	public delegate void CommandDoneEventHandler (object sender, CommandDoneEventArgs e);

	public class Connector
	{
		public Gtk.Window Parent { get; set; }

		public string Hostname { get; set; }

		public int Port { get; set; }

		public bool IsConnected {
			get {
				return client != null && client.Connected;
			}
		}

		public event EventHandler Connected;
		public event EventHandler Disconnected;
		public event UnhandledExceptionEventHandler ConnectionError;
		public event CommandEventHandler CommandExecuting;
		public event CommandEventHandler CommandFail;
		public event CommandDoneEventHandler CommandDone;


		TcpClient client;
		Thread receiverThread, checkThread;

		public Connector (Gtk.Window parent)
		{
			Parent = parent;
		}

		public Connector (Gtk.Window parent, string hostname, int port)
			: this (parent)
		{
			Hostname = hostname;
			Port = port;
		}

		public void Connect ()
		{
			client = new TcpClient (Hostname, Port);

			checkThread = new Thread (() => {
				var stream = client.GetStream ();
				stream.WriteTimeout = 1;
				while (checkThread.ThreadState != ThreadState.AbortRequested) {
					try {
						stream.WriteByte (0);
					} catch (InvalidOperationException ex) {
						if (ConnectionError != null)
							ConnectionError (this, new UnhandledExceptionEventArgs (ex, true));
						Disconnect ();
					}
					Thread.Sleep (1000);
				}
			});
			checkThread.Start ();

			receiverThread = new Thread (() => {
				var stream = client.GetStream ();
				while (receiverThread.ThreadState != ThreadState.AbortRequested) {
					var readBuffer = new byte[2048];
					int bytesCount = 0;
					try {
						bytesCount = stream.Read (readBuffer, 0, readBuffer.Length);
					} catch (Exception) {
						return;
					}
					if (bytesCount == 0) {
						Disconnect ();
						return;
					}
					string msg = Encoding.UTF8.GetString (readBuffer, 0, bytesCount);
					if (!msg.Contains ("|"))
						continue;

					var msgParts = msg.Split ('|');
					if (msgParts [0] == "OK") {
						if (CommandDone != null) {
							CommandDoneEventArgs commandArgs = null;
							commandArgs = msgParts.Length == 4 ?
									new CommandDoneEventArgs (msgParts [1], msgParts [2], msgParts [3]) : 
									new CommandDoneEventArgs (msgParts [1], msgParts [2]);

							Gtk.Application.Invoke ((sender, e) => CommandDone (this, commandArgs));
						}
					} else if (msgParts [0] == "ERR") {
						if (CommandFail != null) {
							CommandEventArgs commandArgs = null;
							commandArgs = msgParts.Length == 3 ?
									new CommandEventArgs (msgParts [1], msgParts [2]) : 
									new CommandEventArgs (msgParts [1]);

							Gtk.Application.Invoke ((sender, e) => CommandFail (this, commandArgs));
						}
					} else if (msgParts [0] == "EXEC") {
						if (CommandExecuting != null) {
							CommandEventArgs commandArgs = new CommandEventArgs (msgParts [1]);
							Gtk.Application.Invoke ((sender, e) => CommandExecuting (this, commandArgs));
						}
					}
				}
			});
			receiverThread.Start ();
			if (Connected != null)
				Connected (this, new EventArgs ());
		}

		public void Disconnect ()
		{
			if (!IsConnected)
				return;
			checkThread.Abort ();
			receiverThread.Abort ();
			client.Close ();
			if (Disconnected != null)
				Disconnected (this, new EventArgs ());
		}

		public void Send (string msg)
		{
			try {
				var msgBytes = Encoding.ASCII.GetBytes (msg);
				client.Client.Send (msgBytes);
			} catch (Exception ex) {
				if (ConnectionError != null)
					ConnectionError (this, new UnhandledExceptionEventArgs (ex, true));
				Disconnect ();
			}
		}
	}
}

