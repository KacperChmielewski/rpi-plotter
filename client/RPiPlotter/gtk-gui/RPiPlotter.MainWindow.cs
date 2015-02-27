
// This file has been generated by the GUI designer. Do not modify.
namespace RPiPlotter
{
	public partial class MainWindow
	{
		private global::Gtk.UIManager UIManager;
		
		private global::Gtk.Action PlotterAction;
		
		private global::Gtk.Action ViewAction;
		
		private global::Gtk.Action HelpAction;
		
		private global::Gtk.Action connectAction;
		
		private global::Gtk.Action disconnectAction;
		
		private global::Gtk.Action quitAction;
		
		private global::Gtk.RadioAction CommandModeAction;
		
		private global::Gtk.RadioAction ControlModeAction;
		
		private global::Gtk.RadioAction SVGModeAction;
		
		private global::Gtk.Action aboutAction;
		
		private global::Gtk.Action CommandReferenceAction;
		
		private global::Gtk.VBox mainvbox;
		
		private global::Gtk.MenuBar menubar;
		
		private global::Gtk.Alignment contentAlignment;
		
		private global::Gtk.VBox contentvbox;
		
		private global::Gtk.ScrolledWindow GtkScrolledWindow;
		
		private global::Gtk.TreeView commandTreeView;
		
		private global::Gtk.HBox commandhbox;
		
		private global::Gtk.Label label1;
		
		private global::Gtk.Entry commandEntry;
		
		private global::Gtk.Button sendcommandButton;
		
		private global::Gtk.Button panicButton;

		protected virtual void Build ()
		{
			global::Stetic.Gui.Initialize (this);
			// Widget RPiPlotter.MainWindow
			this.UIManager = new global::Gtk.UIManager ();
			global::Gtk.ActionGroup w1 = new global::Gtk.ActionGroup ("Default");
			this.PlotterAction = new global::Gtk.Action ("PlotterAction", global::Mono.Unix.Catalog.GetString ("Plotter"), null, null);
			this.PlotterAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Plotter");
			w1.Add (this.PlotterAction, null);
			this.ViewAction = new global::Gtk.Action ("ViewAction", global::Mono.Unix.Catalog.GetString ("View"), null, null);
			this.ViewAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("View");
			w1.Add (this.ViewAction, null);
			this.HelpAction = new global::Gtk.Action ("HelpAction", global::Mono.Unix.Catalog.GetString ("Help"), null, null);
			this.HelpAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Help");
			w1.Add (this.HelpAction, null);
			this.connectAction = new global::Gtk.Action ("connectAction", global::Mono.Unix.Catalog.GetString ("Connect..."), null, "gtk-connect");
			this.connectAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Connect...");
			w1.Add (this.connectAction, "<Primary><Mod2>c");
			this.disconnectAction = new global::Gtk.Action ("disconnectAction", global::Mono.Unix.Catalog.GetString ("Disconnect"), null, "gtk-disconnect");
			this.disconnectAction.Sensitive = false;
			this.disconnectAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Disconnect");
			w1.Add (this.disconnectAction, "<Primary><Mod2>d");
			this.quitAction = new global::Gtk.Action ("quitAction", global::Mono.Unix.Catalog.GetString ("Quit"), null, "gtk-quit");
			this.quitAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Quit");
			w1.Add (this.quitAction, "<Primary><Mod2>q");
			this.CommandModeAction = new global::Gtk.RadioAction ("CommandModeAction", global::Mono.Unix.Catalog.GetString ("Command mode"), null, null, 0);
			this.CommandModeAction.Group = new global::GLib.SList (global::System.IntPtr.Zero);
			this.CommandModeAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Command mode");
			w1.Add (this.CommandModeAction, null);
			this.ControlModeAction = new global::Gtk.RadioAction ("ControlModeAction", global::Mono.Unix.Catalog.GetString ("Control mode"), null, null, 0);
			this.ControlModeAction.Group = this.CommandModeAction.Group;
			this.ControlModeAction.Sensitive = false;
			this.ControlModeAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Control mode");
			w1.Add (this.ControlModeAction, null);
			this.SVGModeAction = new global::Gtk.RadioAction ("SVGModeAction", global::Mono.Unix.Catalog.GetString ("SVG mode"), null, null, 0);
			this.SVGModeAction.Group = this.ControlModeAction.Group;
			this.SVGModeAction.Sensitive = false;
			this.SVGModeAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("SVG mode");
			this.SVGModeAction.Visible = false;
			w1.Add (this.SVGModeAction, null);
			this.aboutAction = new global::Gtk.Action ("aboutAction", global::Mono.Unix.Catalog.GetString ("About"), null, "gtk-about");
			this.aboutAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("About");
			w1.Add (this.aboutAction, null);
			this.CommandReferenceAction = new global::Gtk.Action ("CommandReferenceAction", global::Mono.Unix.Catalog.GetString ("Command reference"), null, null);
			this.CommandReferenceAction.ShortLabel = global::Mono.Unix.Catalog.GetString ("Command reference");
			w1.Add (this.CommandReferenceAction, null);
			this.UIManager.InsertActionGroup (w1, 0);
			this.AddAccelGroup (this.UIManager.AccelGroup);
			this.Name = "RPiPlotter.MainWindow";
			this.Title = global::Mono.Unix.Catalog.GetString ("RPi Plotter Controller");
			this.WindowPosition = ((global::Gtk.WindowPosition)(4));
			// Container child RPiPlotter.MainWindow.Gtk.Container+ContainerChild
			this.mainvbox = new global::Gtk.VBox ();
			this.mainvbox.Name = "mainvbox";
			this.mainvbox.Spacing = 6;
			// Container child mainvbox.Gtk.Box+BoxChild
			this.UIManager.AddUiFromString ("<ui><menubar name='menubar'><menu name='PlotterAction' action='PlotterAction'><menuitem name='connectAction' action='connectAction'/><menuitem name='disconnectAction' action='disconnectAction'/><separator/><menuitem name='quitAction' action='quitAction'/></menu><menu name='ViewAction' action='ViewAction'><menuitem name='CommandModeAction' action='CommandModeAction'/><menuitem name='ControlModeAction' action='ControlModeAction'/><menuitem name='SVGModeAction' action='SVGModeAction'/></menu><menu name='HelpAction' action='HelpAction'><menuitem name='CommandReferenceAction' action='CommandReferenceAction'/><separator/><menuitem name='aboutAction' action='aboutAction'/></menu></menubar></ui>");
			this.menubar = ((global::Gtk.MenuBar)(this.UIManager.GetWidget ("/menubar")));
			this.menubar.Name = "menubar";
			this.mainvbox.Add (this.menubar);
			global::Gtk.Box.BoxChild w2 = ((global::Gtk.Box.BoxChild)(this.mainvbox [this.menubar]));
			w2.Position = 0;
			w2.Expand = false;
			w2.Fill = false;
			// Container child mainvbox.Gtk.Box+BoxChild
			this.contentAlignment = new global::Gtk.Alignment (0.5F, 0.5F, 1F, 1F);
			this.contentAlignment.Name = "contentAlignment";
			this.contentAlignment.LeftPadding = ((uint)(6));
			this.contentAlignment.RightPadding = ((uint)(6));
			this.contentAlignment.BottomPadding = ((uint)(6));
			// Container child contentAlignment.Gtk.Container+ContainerChild
			this.contentvbox = new global::Gtk.VBox ();
			this.contentvbox.Sensitive = false;
			this.contentvbox.Name = "contentvbox";
			this.contentvbox.Spacing = 6;
			// Container child contentvbox.Gtk.Box+BoxChild
			this.GtkScrolledWindow = new global::Gtk.ScrolledWindow ();
			this.GtkScrolledWindow.Name = "GtkScrolledWindow";
			this.GtkScrolledWindow.ShadowType = ((global::Gtk.ShadowType)(1));
			// Container child GtkScrolledWindow.Gtk.Container+ContainerChild
			this.commandTreeView = new global::Gtk.TreeView ();
			this.commandTreeView.CanFocus = true;
			this.commandTreeView.Name = "commandTreeView";
			this.commandTreeView.EnableSearch = false;
			this.GtkScrolledWindow.Add (this.commandTreeView);
			this.contentvbox.Add (this.GtkScrolledWindow);
			global::Gtk.Box.BoxChild w4 = ((global::Gtk.Box.BoxChild)(this.contentvbox [this.GtkScrolledWindow]));
			w4.Position = 0;
			// Container child contentvbox.Gtk.Box+BoxChild
			this.commandhbox = new global::Gtk.HBox ();
			this.commandhbox.Name = "commandhbox";
			this.commandhbox.Spacing = 6;
			// Container child commandhbox.Gtk.Box+BoxChild
			this.label1 = new global::Gtk.Label ();
			this.label1.Name = "label1";
			this.label1.LabelProp = global::Mono.Unix.Catalog.GetString ("Command:");
			this.commandhbox.Add (this.label1);
			global::Gtk.Box.BoxChild w5 = ((global::Gtk.Box.BoxChild)(this.commandhbox [this.label1]));
			w5.Position = 0;
			w5.Expand = false;
			w5.Fill = false;
			// Container child commandhbox.Gtk.Box+BoxChild
			this.commandEntry = new global::Gtk.Entry ();
			this.commandEntry.CanFocus = true;
			this.commandEntry.Name = "commandEntry";
			this.commandEntry.IsEditable = true;
			this.commandEntry.InvisibleChar = '●';
			this.commandhbox.Add (this.commandEntry);
			global::Gtk.Box.BoxChild w6 = ((global::Gtk.Box.BoxChild)(this.commandhbox [this.commandEntry]));
			w6.Position = 1;
			// Container child commandhbox.Gtk.Box+BoxChild
			this.sendcommandButton = new global::Gtk.Button ();
			this.sendcommandButton.CanFocus = true;
			this.sendcommandButton.Name = "sendcommandButton";
			this.sendcommandButton.UseUnderline = true;
			this.sendcommandButton.Label = global::Mono.Unix.Catalog.GetString ("Send");
			this.commandhbox.Add (this.sendcommandButton);
			global::Gtk.Box.BoxChild w7 = ((global::Gtk.Box.BoxChild)(this.commandhbox [this.sendcommandButton]));
			w7.Position = 2;
			w7.Expand = false;
			w7.Fill = false;
			// Container child commandhbox.Gtk.Box+BoxChild
			this.panicButton = new global::Gtk.Button ();
			this.panicButton.CanFocus = true;
			this.panicButton.Name = "panicButton";
			this.panicButton.UseUnderline = true;
			this.panicButton.Label = global::Mono.Unix.Catalog.GetString ("PANIC!");
			this.commandhbox.Add (this.panicButton);
			global::Gtk.Box.BoxChild w8 = ((global::Gtk.Box.BoxChild)(this.commandhbox [this.panicButton]));
			w8.Position = 3;
			w8.Expand = false;
			w8.Fill = false;
			this.contentvbox.Add (this.commandhbox);
			global::Gtk.Box.BoxChild w9 = ((global::Gtk.Box.BoxChild)(this.contentvbox [this.commandhbox]));
			w9.Position = 1;
			w9.Expand = false;
			w9.Fill = false;
			this.contentAlignment.Add (this.contentvbox);
			this.mainvbox.Add (this.contentAlignment);
			global::Gtk.Box.BoxChild w11 = ((global::Gtk.Box.BoxChild)(this.mainvbox [this.contentAlignment]));
			w11.Position = 1;
			this.Add (this.mainvbox);
			if ((this.Child != null)) {
				this.Child.ShowAll ();
			}
			this.DefaultWidth = 448;
			this.DefaultHeight = 299;
			this.Show ();
			this.DeleteEvent += new global::Gtk.DeleteEventHandler (this.OnQuit);
			this.connectAction.Activated += new global::System.EventHandler (this.OnConnectActionActivated);
			this.quitAction.Activated += new global::System.EventHandler (this.OnQuit);
		}
	}
}
