using System;
using System.Xml;
using System.IO;
using System.Text;
using System.Threading;

namespace RPiPlotter.Windows
{
    public sealed partial class PreviewWindow : Gtk.Window
    {
        XmlElement pathElement, executingPathElement;
        XmlDocument document;
        string tempPath = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "vPlotter_preview.svg");
        bool isRefreshing = false;

        public string ExecutingPathData
        {
            get
            {
                return executingPathElement != null ? executingPathElement.GetAttribute("d") : "";
            }
            set
            {
                if (executingPathElement != null && executingPathElement.GetAttribute("d") != value)
                {
                    SetExecutingPathData(value, true);
                }
            }
        }

        public string PathData
        {
            get
            {
                return pathElement != null ? pathElement.GetAttribute("d") : "";
            }
            set
            {
                if (pathElement != null && pathElement.GetAttribute("d") != value)
                {
                    SetPathData(value, true);
                }
            }
        }

        public PreviewWindow()
            : base(Gtk.WindowType.Toplevel)
        {
            this.Build();
            InitDocument();
            new Thread(RefreshPreview).Start();
        }

        public void InitDocument()
        {
            document = new XmlDocument();
            document.AppendChild(document.CreateXmlDeclaration("1.0", "UTF-8", "no"));
            var svg = document.CreateElement("svg");
            document.AppendChild(svg);
            svg.SetAttribute("xmlns", "http://www.w3.org/2000/svg");
            svg.SetAttribute("version", "1.1");
            svg.SetAttribute("width", "210mm");
            svg.SetAttribute("height", "297mm");
            var backgroundRect = document.CreateElement("rect");
            svg.AppendChild(backgroundRect);
            backgroundRect.SetAttribute("width", "100%");
            backgroundRect.SetAttribute("height", "100%");
            backgroundRect.SetAttribute("style", "fill:white;stroke:black;stroke-width:2px;");
            var g = document.CreateElement("g");
            executingPathElement = document.CreateElement("path");
            executingPathElement.SetAttribute("style", "fill:none;stroke:blue;stroke-width:2px;stroke-dasharray:10 10;");
            g.AppendChild(executingPathElement);
            pathElement = document.CreateElement("path");
            pathElement.SetAttribute("style", "stroke:#000000;stroke-width:3px;fill:none;");
            g.AppendChild(pathElement);
            svg.AppendChild(g);
        }

        void SetExecutingPathData(string value, bool refresh = true)
        {
            executingPathElement.SetAttribute("d", value);
            if (refresh)
                new Thread(RefreshPreview).Start();
        }

        void SetPathData(string value, bool refresh = true)
        {
            pathElement.SetAttribute("d", value);
            if (refresh)
                new Thread(RefreshPreview).Start();
        }

        public void ClearPaths()
        {
            SetExecutingPathData("", false);
            SetPathData("", true);
        }

        public void RefreshPreview()
        {
            while (isRefreshing)
                Thread.Sleep(100);
            
            isRefreshing = true;

            try
            {
                using (var sw = new StreamWriter(tempPath))
                {
                    sw.Write(document.OuterXml);
                    sw.Flush();
                }   
                var pixbuf = Rsvg.Tool.PixbufFromFileAtZoom(tempPath, 0.8, 0.8);
                Gtk.Application.Invoke((sender, e) =>
                    {
                        previewImage.Pixbuf = pixbuf;
                    });
            }
            finally
            {
                isRefreshing = false;
            }
        }
    }
}

