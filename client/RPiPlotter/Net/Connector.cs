using System;
using System.Net.Sockets;
using System.Threading;
using System.Text;
using System.IO;

namespace RPiPlotter.Net
{
    public delegate void CommandEventHandler(object sender,CommandEventArgs e);
    public delegate void CommandDoneEventHandler(object sender,CommandDoneEventArgs e);
    public delegate void DisconnectedEventHandler(object sender,DisconnectedEventArgs e);
    public delegate void MessageReceivedEventHandler(object sender,MessageReceivedEventArgs e);

    public class Connector
    {
        public Gtk.Window Parent { get; set; }

        public string Hostname { get; set; }

        public int Port { get; set; }

        public bool IsConnected
        {
            get
            {
                return client != null && client.Connected;
            }
        }

        public event EventHandler Connected;
        public event DisconnectedEventHandler Disconnected;
        public event UnhandledExceptionEventHandler ConnectionError;
        public event CommandEventHandler CommandExecuting;
        public event CommandEventHandler CommandFail;
        public event CommandDoneEventHandler CommandDone;
        public event MessageReceivedEventHandler MessageReceived;


        TcpClient client;
        Thread receiverThread, checkThread;
        int _counter = 0;

        public Connector(Gtk.Window parent)
        {
            Parent = parent;
        }

        public Connector(Gtk.Window parent, string hostname, int port)
            : this(parent)
        {
            Hostname = hostname;
            Port = port;
        }

        public void Connect()
        {
            client = new TcpClient(Hostname, Port);

            checkThread = new Thread(() =>
                {
                    var stream = client.GetStream();
                    stream.WriteTimeout = 500;

                    try
                    {   
                        while (checkThread.ThreadState != ThreadState.AbortRequested)
                        {
                            stream.Write(new byte[] { 1 }, 0, 1);
                            Thread.Sleep(1000);
                        }
                    }
                    catch (IOException ex)
                    {
                        Disconnect();
                        if (ConnectionError != null)
                            ConnectionError(this, new UnhandledExceptionEventArgs(ex, true));
                        
                    }
                });
            checkThread.Start();

            receiverThread = new Thread(() =>
                {
                    var stream = client.GetStream();
                    while (IsConnected)
                    {
                        var readBuffer = new byte[16384];
                        int bytesCount = 0;
                        try
                        {
                            bytesCount = stream.Read(readBuffer, 0, readBuffer.Length);
                        }
                        catch (Exception)
                        {
                            return;
                        }
                        if (bytesCount == 0)
                        {
                            if (IsConnected)
                                Disconnect(true);
                            return;
                        }
                        string message = Encoding.UTF8.GetString(readBuffer, 0, bytesCount);

                        foreach (string msg in message.Split(new string[] {";;"}, StringSplitOptions.RemoveEmptyEntries))
                        {
                            if (!msg.Contains("|"))
                                continue;

                            var msgParts = msg.Split('|');
                            if (msgParts[0] == "OK")
                            {
                                if (CommandDone != null)
                                {
                                    CommandDoneEventArgs commandArgs = null;
                                    var cmdIndex = int.Parse(msgParts[1]);
                                    commandArgs = msgParts.Length == 4 ?
                                        new CommandDoneEventArgs(cmdIndex, msgParts[2], msgParts[3]) : 
                                        new CommandDoneEventArgs(cmdIndex, msgParts[2]);

                                    Gtk.Application.Invoke((sender, e) => CommandDone(this, commandArgs));
                                }
                            }
                            else if (msgParts[0] == "ERR")
                            {
                                if (CommandFail != null)
                                {
                                    CommandEventArgs commandArgs = null;
                                    var cmdIndex = int.Parse(msgParts[1]);
                                    commandArgs = msgParts.Length == 3 ?
                                        new CommandEventArgs(cmdIndex, msgParts[2]) : 
                                        new CommandEventArgs(cmdIndex);

                                    Gtk.Application.Invoke((sender, e) => CommandFail(this, commandArgs));
                                }
                            }
                            else if (msgParts[0] == "EXEC")
                            {
                                if (CommandExecuting != null)
                                {
                                    var commandArgs = new CommandEventArgs(int.Parse(msgParts[1]));
                                    Gtk.Application.Invoke((sender, e) => CommandExecuting(this, commandArgs));
                                }
                            }
                            else if (msgParts[0] == "MSG")
                            {
                                if (MessageReceived != null)
                                {
                                    var commandArgs = new MessageReceivedEventArgs(msgParts[1]);
                                    Gtk.Application.Invoke((sender, e) => MessageReceived(this, commandArgs));
                                }
                            }
                        }
                    }
                });
            receiverThread.Start();
            if (Connected != null)
                Connected(this, new EventArgs());
        }

        public void Disconnect(bool serverDisconnect = false)
        {
            if (checkThread != null)
                checkThread.Abort();
            if (client != null && client.Connected)
                client.Close();
            if (Disconnected != null)
                Gtk.Application.Invoke((sender, e) =>
                    Disconnected(this, new DisconnectedEventArgs(serverDisconnect)));
            
        }

        public void SendServerCommand(string msg)
        {
            try
            {
                var msgBytes = Encoding.ASCII.GetBytes("!" + msg);
                client.Client.Send(msgBytes);
            }
            catch (Exception ex)
            {
                if (ConnectionError != null)
                    ConnectionError(this, new UnhandledExceptionEventArgs(ex, true));
                Disconnect();
            }
        }

        public int Send(string msg)
        {
            try
            {
                var msgBytes = Encoding.ASCII.GetBytes(_counter + "|" + msg);
                client.Client.Send(msgBytes);
            }
            catch (Exception ex)
            {
                if (ConnectionError != null)
                    ConnectionError(this, new UnhandledExceptionEventArgs(ex, true));
                Disconnect();
                return -1;
            }
            return _counter++;
        }
    }
}

