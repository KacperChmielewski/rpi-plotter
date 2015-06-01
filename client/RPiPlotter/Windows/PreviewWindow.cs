using System;
using System.Xml;

namespace RPiPlotter
{
	public partial class PreviewWindow : Gtk.Window
	{
		public PreviewWindow () :
			base (Gtk.WindowType.Toplevel)
		{
			this.Build ();
			Rsvg.Tool.PixbufFromFile ();
		}

		public void SetPathData (string data)
		{
			XmlDocument doc = new XmlDocument ();
			doc.InnerXml = "<svg xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\"></svg>";
			var path = doc.CreateElement ("path");
			var d = doc.CreateAttribute ("d");
			d.InnerText = data;
		}
	}
}

