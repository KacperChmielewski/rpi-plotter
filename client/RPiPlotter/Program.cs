using System;
using Gtk;

namespace RPiPlotter
{
    class MainClass
    {
        public static void Main(string[] args)
        {
            Application.Init();
            MainWindow win = new MainWindow();
            win.Show();
            GLib.ExceptionManager.UnhandledException += (e) =>
            {
                var ex = (Exception)e.ExceptionObject;
                Console.Error.WriteLine("Error: " + ex.Message + "\n\nStacktrace:" + ex.StackTrace);
                var dialog = new Gtk.MessageDialog(win,
                                 Gtk.DialogFlags.DestroyWithParent,
                                 Gtk.MessageType.Error,
                                 Gtk.ButtonsType.Ok,
                                 ex.Message + "\n\n" + "See console for more details.");
                dialog.Run();
                dialog.Destroy();
                if (e.IsTerminating)
                    e.ExitApplication = true;
            };
            Application.Run();
        }
    }
}
