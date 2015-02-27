using System;
using System.Net.Sockets;
using System.Threading;
using System.Text;

namespace RPiPlotter
{
	public class Connector
	{
		public Gtk.Window Parent { get; set; }

		public string Hostname { get; set; }

		public int Port { get; set; }

		public event EventHandler Connected;
		public event UnhandledExceptionEventHandler ConnectionError;


		TcpClient client;
		Thread receiverThread;

		public Connector(Gtk.Window parent)
		{
			Parent = parent;
		}

		public Connector(Gtk.Window parent, string hostname, int port)
			: this (parent)
		{
			Hostname = hostname;
			Port = port;
		}

		public void Connect()
		{
			client = new TcpClient ();
			var result = client.BeginConnect(Hostname, Port, null, null);

			var success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromSeconds(1));

			if (!success)
			{
				throw new Exception("Failed to connect.");
			}

			// we have connected
			client.EndConnect(result);

			receiverThread = new Thread (() => {
				var stream = client.GetStream ();
				while (receiverThread.ThreadState != ThreadState.AbortRequested) {
					if (stream.DataAvailable) {
						var readBuffer = new byte[1024];
						int bytesCount = stream.Read (readBuffer, 0, readBuffer.Length);
						string msg = Encoding.UTF8.GetString (readBuffer, 0, bytesCount);
						Gtk.Application.Invoke ((sender, e) => {
							var dialog = new Gtk.MessageDialog (Parent, Gtk.DialogFlags.DestroyWithParent, Gtk.MessageType.Info, Gtk.ButtonsType.Ok, msg);
							dialog.Run ();
							dialog.Destroy ();
						});
					}
					Thread.Sleep (10);
				}
			});
			receiverThread.Start ();
			if (Connected != null)
				Connected (this, new EventArgs ());
		}

		public void Disconnect()
		{
			receiverThread.Abort ();
			client.Close ();
		}

		public void Send()
		{
			try {

			} catch (Exception ex) {

			}
		}
	}
}

