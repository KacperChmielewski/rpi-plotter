using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Globalization;

namespace RPiPlotter.Common
{
    public static class UnitConverter
    {
        static readonly Dictionary<Unit, double> _unitsValues = new Dictionary<Unit, double>()
        {
            { Unit.Points, (3200.0d / 79.0d) * 0.352777778 },
            { Unit.Centimeters, (3200.0d / 79.0d) * 10.0d },
            { Unit.Inches, (3200.0d / 79) * 25.4 },
            { Unit.Milimeters, 3200.0d / 79.0d }
        };

        public static Dictionary<Unit, double> UnitsValues
        {
            get
            {
                return _unitsValues;
            }
        }

        public static string ToSteps(string command, Unit unit)
        {
            if (unit == Unit.None)
            {
                return command;
            }
            string newCommand = "";
            var unitValue = UnitsValues[unit];
            var cmdList = Regex.Matches(command, @"([A-Za-z]+)\s*((?:-?(\d((E|e)(\+|\-)\d+)?)*\.?(?:\s|,)*)*)");
            foreach (Match cmdMatch in cmdList)
            {
                var cmd = cmdMatch.Value;
                if (Regex.IsMatch(cmd, "[A-Za-z]{2,}"))
                    continue;
                foreach (Match m in Regex.Matches(cmd, @"[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?"))
                {
                    var value = m.Value.Trim();
                    if (value == "0")
                        continue;
                    var parsedNum = double.Parse(value, CultureInfo.InvariantCulture);
                    var converted = Math.Round(parsedNum * unitValue);
                    var index = cmd.IndexOf(value);
                    cmd = cmd.Remove(index, m.Length);
                    cmd = cmd.Insert(index, Math.Round(converted).ToString());
                }
                newCommand += cmd;
            }
            return newCommand;

        }

    }

    public enum Unit
    {
        None,
        Points,
        Centimeters,
        Inches,
        Milimeters
    }
}

