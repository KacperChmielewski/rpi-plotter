from threading import Thread
import re
import time
import argparse
import configparser
import os
import ast
import sys
import logging

from mathextra import *
import hardware as hw

RE_CMDARGS = re.compile('[\+\-\w\.]+')
RE_CMD = re.compile(r'([A-Za-z]+)\s*((?:-?(\d((E|e)(\+|\-)\d+)?)*\.?(?:\s|,)*)*)')


class Plotter:
    m1, m2 = [0, 0], [81013, 0]
    spr = 200  # steps per revolution in full step mode
    ms = 16  # (1, 2, 4, 8, 16)
    curve_acc = 0.01
    speed = 1
    sr, atxpower, separator = None, None, None
    right_engine, left_engine = None, None

    def __init__(self, parentparser=None, init_hw=True):
        if not parentparser:
            parentparser = argparse.ArgumentParser(add_help=False)
        parser = argparse.ArgumentParser(description="Software controller for vPlotter",
                                         epilog="Happy plotting!",
                                         parents=[parentparser],
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        mutuals_info = parser.add_mutually_exclusive_group()
        mutuals_info.add_argument('-d', '--debug', default=False, action='store_true',
                                  help="display more information", dest='debug')
        mutuals_info.add_argument('-s', '--silent', default=False, help='silent mode (print errors only)',
                                  dest='silent', action='store_true')
        parser.add_argument('--no-logging', default=False, action='store_true', help="disable logging to file")

        group_plotter = parser.add_argument_group("Plotter")
        group_plotter.add_argument("-C", "--calibrate", nargs=2, metavar=('<x>', '<y>'), dest='calpoint',
                                   help="calibrate at <x>,<y> on start")
        group_plotter.add_argument('-i', type=int, dest='poweroff_interval', metavar='<n>', default=15,
                                   help="power off after <n> seconds, when idle")
        group_plotter.add_argument("--no-power", action='store_true',
                                   help="start without power")

        group_state = parser.add_argument_group("State")
        mutuals_state = group_state.add_mutually_exclusive_group()
        mutuals_state.add_argument('--fresh-state', action='store_true',
                                   help="create fresh state file")
        mutuals_state.add_argument('--no-state', action='store_true',
                                   help="ignore state file")
        self.args = parser.parse_args()

        self.calibrated = False
        self.power = False
        self._execpause, self._execstop = False, False
        self.startpoint, self.controlpoint = None, None
        self.offset = (0, 0)
        self.poweroff_interval = 15

        self.statepath = None

        # SVG Path Data and plotter specific commands
        # http://www.w3.org/TR/SVGTiny12/paths.html
        self.commands = {  # commandname: (action, argument_count)
                           # SVG Path Data
                           'M': (self.moveto, 2),
                           'm': (self.moveto_rel, 2),
                           'L': (self.lineto, 2),
                           'l': (self.lineto_rel, 2),
                           'V': (self.vertical, 1),
                           'v': (self.vertical_rel, 1),
                           'H': (self.horizontal, 1),
                           'h': (self.horizontal_rel, 1),
                           'Z': (self.closepath, 0),
                           'z': (self.closepath, 0),
                           'C': (self.curveto, 6),
                           'c': (self.curveto_rel, 6),
                           'S': (self.scurveto, 4),
                           's': (self.scurveto_rel, 4),
                           'Q': (self.curveto, 4),
                           'q': (self.curveto_rel, 4),
                           'T': (self.scurveto, 2),
                           't': (self.scurveto_rel, 2),
                           'A': (self.arc, 7),
                           'a': (self.arc_rel, 7),

                           # Plotter
                           'SLP': (time.sleep, 1),
                           'SEP': (self.setseparator, 1),
                           'CAL': (self.calibrate, 2),
                           'COR': (self.getcoord, 0),
                           'LEN': (self.getlength, 0),
                           'PWR': (self.setpower, 1),
                           'OFF': (self.setoffset, 0),
                           'OFC': (self.clearoffset, 0)
        }

        self.logger = logging.getLogger("vPlotter")
        self.logger.setLevel(logging.DEBUG)

        if not self.args.no_logging:
            fh = logging.FileHandler("debug.log")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s"))
            self.logger.addHandler(fh)
        ch = logging.StreamHandler()
        if self.args.debug:
            ch.setLevel(logging.DEBUG)
        elif self.args.silent:
            ch.setLevel(logging.WARNING)
        else:
            ch.setLevel(logging.INFO)
        self.logger.addHandler(ch)

        if self.args.no_state:
            self.logger.info("Skipping state load...")
        else:
            self.statepath = os.path.expanduser('~/.config/vPlotter')
            if not os.path.exists(self.statepath):
                os.makedirs(self.statepath)
            self.statepath = os.path.join(self.statepath, "state.conf")
            self.loadstate()

        if self.args.poweroff_interval != self.poweroff_interval:
            self.poweroff_interval = self.args.poweroff_interval
        self.poweroffthread = self.PowerOffThread(self.poweroff_interval, self.getpower, self.setpower)
        if init_hw:
            self.init_hw()

    def init_hw(self):
        self.logger.debug("Initializing shift register...")
        self.sr = hw.ShiftRegister(15, 11, 13, 2)

        self.logger.debug("Initializing ATX power supply...")
        self.atxpower = hw.ATX(7, 15, self.sr)

        self.logger.debug("Initializing left engine...")
        self.left_engine = hw.A4988(26, 24, 14, 13, 12, 11, 10, 9, self.sr, side=0, revdir=True)
        self.logger.debug("Initializing right engine...")
        self.right_engine = hw.A4988(18, 16, 6, 5, 4, 3, 2, 1, self.sr, side=1)

        self.logger.debug("Initializing separator...")
        self.separator = hw.Servo(23)
        if self.args.calpoint:
            self.calibrate(self.args.calpoint[0], self.args.calpoint[1])

        if not self.args.no_power:
            self.setpower(True)
        self.poweroffthread.start()

    def shutdown(self):
        if not self.args.no_state:
            self.savestate()
        self.setpower(False)

    def loadstate(self):
        if self.args.fresh_state or not os.path.isfile(self.statepath):
            self.logger.info("Creating new state file in " + self.statepath + " ...")
            open(self.statepath, 'w').close()
        else:
            config = configparser.ConfigParser()
            config.read_file(open(self.statepath))
            if not config.has_section("Plotter"):
                self.logger.warning("Invalid state file: " + self.statepath + "\nCreating new ...")
                config.clear()
                return

            self.logger.info("Reading state from " + self.statepath + " ...")
            try:
                p = config["Plotter"]

                length = ast.literal_eval(p['Length'])
                offset = ast.literal_eval(p['Offset'])
                poweroff_interval = int(p['Poweroff interval'])
                hw.length = length
                self.offset = offset
                if length != [0, 0]:
                    self.calibrated = True
                self.poweroff_interval = poweroff_interval
            except KeyError:
                self.logger.error("Cannot load " + self.statepath + " state file! Using default values instead.")

    def savestate(self):
        config = configparser.ConfigParser()
        config["Plotter"] = {
            'Length': str(hw.length),
            'Offset': str(self.offset),
            'Poweroff interval': self.poweroff_interval
        }
        with open(self.statepath, 'w') as configfile:
            configfile.write("### vPlotter State File\n### DO NOT MODIFY THIS FILE!!!\n\n")
            config.write(configfile)
            self.logger.info("State saved to " + self.statepath)

    def move(self, left, right, speed):
        if not self.getpower():
            self.setpower(True)
        gleft = int(left)
        gright = int(right)
        speed = float(speed)
        if gleft == 0 or gright == 0:
            # move
            self.left_engine.move(gleft, speed)
            self.right_engine.move(gright, speed)
        else:
            rel = abs(float(gleft) / gright)
            done = 0
            ldir = sign(gleft)  # Left Direction
            rdir = sign(gright)  # Right Direction
            if ldir == -1:
                ldir = 0
            self.left_engine.direction = ldir
            if rdir == -1:
                rdir = 0
            self.right_engine.direction = rdir
            for i in range(1, abs(gright) + 1):
                if self._execstop:
                    self._execstop = False
                    raise ExecutionError()
                while self.getexecpause():
                    time.sleep(0.1)
                self.right_engine.move(1, speed)
                htbd = int(i * rel)  # steps which Has To Be Done
                td = htbd - done  # steps To Do
                self.left_engine.move(td, speed)
                done = htbd

    # // SVG Commands

    def moveto(self, x, y, sep=True, savepoint=True, relative=False):
        if not self.calibrated:
            raise NotCalibratedError()

        if relative:
            currentpos = ltc(hw.length, self.m1, self.m2)
            x += currentpos[0]
            y += currentpos[1]
        else:
            x += self.offset[0]
            y += self.offset[1]

        if not self.startpoint:
            self._savestartpoint()
        if self.controlpoint:
            self.controlpoint = None

        destination = ctl([int(x), int(y)], self.m1, self.m2)
        change = (int(destination[0] - hw.length[0]), int(destination[1] - hw.length[1]))

        self.setseparator(sep)
        if change == (0, 0):
            return
        self.logger.debug("Strings change: " + str(change))
        self.move(change[0], change[1], self.speed)
        if savepoint:
            self._savestartpoint()

    def moveto_rel(self, x, y):
        self.moveto(x, y, True, True, relative=True)

    def lineto(self, x, y):
        self.moveto(x, y, False, False)

    def lineto_rel(self, x, y):
        self.moveto(x, y, False, False, relative=True)

    def vertical(self, y):
        self.moveto(int(self.getcoord()[0]), y, False, False)

    def vertical_rel(self, y):
        self.moveto(0, y, False, False, relative=True)

    def horizontal(self, x):
        self.moveto(x, int(self.getcoord()[1]), False, False)

    def horizontal_rel(self, x):
        self.moveto(x, 0, False, False, relative=True)

    def closepath(self):
        self.moveto(self.startpoint[0], self.startpoint[1], False, False)

    def curveto(self, *points, relative=False):
        start = self.getcoord()
        grp_points = [(points[i], points[i + 1]) for i in range(0, len(points), 2)]  # group to tuples
        if relative:
            grp_points = [(p[0] + start[0], p[1] + start[1]) for p in grp_points]

        if all(p[0] == grp_points[0][0] for p in grp_points) or all(p[1] == grp_points[1][1] for p in grp_points):
            self.moveto(grp_points[0][0], grp_points[0][1], savepoint=False)
            return

        grp_points.insert(0, start)  # add start point

        t = 0
        while t <= 1:
            self.drawcurve(t, grp_points)
            t += self.curve_acc
        self.controlpoint = grp_points[-2]

    def curveto_rel(self, *points):
        self.curveto(*points, relative=True)

    def scurveto(self, *points, relative=False):
        coord = self.getcoord()
        p1 = self._getconpointreflection(coord)

        if relative:
            p1 = (p1[0] - coord[0], p1[1] - coord[1])

        self.curveto(*(p1 + points), relative=relative)

    def scurveto_rel(self, *points):
        self.scurveto(*points, relative=True)

    def arc(self, rx, ry, angle, fa, fs, x, y, cx=None, cy=None):
        if not cx or not cy:
            cx, cy = self.getcoord()
        if cx == x and cy == y:
            return
        if rx == 0 or ry == 0:
            self.lineto(x, y)

        rx = abs(rx)
        ry = abs(ry)

        phi = math.radians(((angle % 360) + 360) % 360)
        cosphi = math.cos(phi)
        sinphi = math.sin(phi)

        x1r = (cosphi * (cx - x) + sinphi * (cy - y)) / 2
        y1r = (-sinphi * (cx - x) + cosphi * (cy - y)) / 2

        _a = (x1r * x1r) / (rx * rx) + (y1r * y1r) / (ry * ry)

        if _a > 1:
            # No solution, scale ellipse up according to SVG standard
            sqrt_a = math.sqrt(_a)
            rx *= sqrt_a
            ry *= sqrt_a
            cxr = 0
            cyr = 0
        else:
            if fa == fs:
                k = float(-1)
            else:
                k = float(1)

            k *= math.sqrt((rx * rx * ry * ry) / ((rx * rx * y1r * y1r) + (ry * ry * x1r * x1r)) - float(1))
            cxr = k * rx * y1r / ry
            cyr = -k * ry * x1r / rx

        cx = cosphi * cxr - sinphi * cyr + (cx + x) / 2
        cy = sinphi * cxr + cosphi * cyr + (cy + y) / 2

        sx = (x1r - cxr) / rx
        sy = (y1r - cyr) / ry
        tx = (-x1r - cxr) / rx
        ty = (-y1r - cyr) / ry
        phi1 = math.atan2(sy, sx)
        phi_delta = (((math.atan2(ty, tx) - phi1) % (math.pi * 2)) + (math.pi * 2)) % (math.pi * 2)
        if not fs:
            phi_delta -= (math.pi * 2)

        # One segment can not cover more that PI, less than PI/2 is
        # recommended to avoid visible inaccuracies caused by rounding errors
        segment_len = math.ceil(abs(phi_delta) / (math.pi * 2) * 4)

        inc = phi_delta / segment_len
        a = math.sin(inc) * (math.sqrt(4 + 3 * (math.tan(inc / 2)) ** 2) - 1) / 3

        sinphi1 = math.sin(phi1)
        cosphi1 = math.cos(phi1)

        p1x = cx
        p1y = cy
        relq1x = a * (-rx * cosphi * sinphi1 - ry * sinphi * cosphi1)
        relq1y = a * (-rx * sinphi * sinphi1 + ry * cosphi * cosphi1)

        for i in range(0, segment_len):
            eta = phi1 + (i + 1) * inc
            sin_eta = math.sin(eta)
            cos_eta = math.cos(eta)

            p2x = cx + rx * cosphi * cos_eta - ry * sinphi * sin_eta
            p2y = cy + rx * sinphi * cos_eta + ry * cosphi * sin_eta
            relq2x = a * (-rx * cosphi * sin_eta - ry * sinphi * cos_eta)
            relq2y = a * (-rx * sinphi * sin_eta + ry * cosphi * cos_eta)

            if i == segment_len - 1:
                p2x = x
                p2y = y

            self.curveto(p1x + relq1x, p1y + relq1y, p2x - relq2x, p2y - relq2y, p2x, p2y)
            # parsePathCode(BEZIER_VERTEX)
            # parsePathVertex(p1x + relq1x, p1y + relq1y)
            # parsePathVertex(p2x - relq2x, p2y - relq2y)
            # parsePathVertex(p2x, p2y)

            p1x = p2x
            relq1x = relq2x
            p1y = p2y
            relq1y = relq2y

    def arc_rel(self, rx, ry, angle, fa, fs, x, y):
        cx, cy = self.getcoord()
        self.arc(rx, ry, angle, fa, fs, x + cx, y + cy, cx, cy)

    # // Helper methods

    def drawcurve(self, t, points):
        if len(points) == 1:
            self.lineto(points[0][0], points[0][1])
            return

        newpoints = []
        for i in range(0, len(points) - 1):
            x = (1 - t) * points[i][0] + t * points[i + 1][0]
            y = (1 - t) * points[i][1] + t * points[i + 1][1]
            newpoints.append((x, y))
        self.drawcurve(t, newpoints)

    def getexecpause(self):
        return self._execpause

    def setexecpause(self, value):
        value = bool(int(value))
        if self._execpause == value:
            return
        self._execpause = value

        if value:
            self.logger.info("Paused")
        else:
            self.logger.info("Unpaused")

    def stopexecute(self):
        self._execstop = True

    def _savestartpoint(self):
        self.startpoint = self.getcoord()

    def _getconpointreflection(self, current=None):
        if not current:
            current = self.getcoord()
        x = current[0] + (current[0] - self.controlpoint[0])
        y = current[1] + (current[1] - self.controlpoint[1])
        return x, y

    # // Plotter commands

    def setseparator(self, state):
        self.separator.set(int(state))

    def calibrate(self, x, y):
        p = (int(x), int(y))
        hw.length = ctl(p, self.m1, self.m2)
        hw.length = [int(hw.length[0]), int(hw.length[1])]
        self.calibrated = True
        self.logger.debug("Calibrated at " + str(p))

    def getcoord(self):
        if self.calibrated:
            x, y = ltc(hw.length, self.m1, self.m2)
            return x - self.offset[0], y - self.offset[1]
        else:
            raise NotCalibratedError()

    @staticmethod
    def getlength():
        return hw.length

    def getpower(self):
        return self.power

    def setpower(self, value):
        value = bool(int(value))
        if self.power == value:
            state = "OFF"
            if value:
                state = "ON"
            self.logger.info("POWER: already turned " + state)
            return
        self.power = value

        state = "off"
        if self.getpower():
            state = "on"
        self.logger.info("POWER: " + state)
        self.atxpower.power(value)
        self.atxpower.loadr(value)
        self.left_engine.power(value)
        self.right_engine.power(value)

    def setoffset(self):
        self.offset = ltc(hw.length, self.m1, self.m2)
        return "Offset set at " + str(self.offset)

    def clearoffset(self):
        self.offset = (0, 0)
        self.logger.info("Offset cleared!")

    # // Main execution command

    def execute(self, command):
        """:type command: str"""
        if self._execstop:
            self._execstop = False
        command = command.strip()
        if len(command) == 0:
            return

        if not command[0].isalpha():
            if len(command) < 15:
                formatlen = len(command)
            else:
                formatlen = 15
            raise CommandError(command[0:formatlen] + " - incorrect format!")

        cmdlist = RE_CMD.findall(command)

        if not cmdlist:
            raise CommandError(command + " - syntax error!")

        action_stack = []
        for c in cmdlist:
            cmdname = c[0]
            c_str = (str(c[0]) + " " + str(c[1])).strip()

            if len(cmdname) > 1:
                cmdname = cmdname.upper()
            cmdinfo = self.commands.get(cmdname)
            if not cmdinfo:
                raise CommandError(c_str + " - bad command!")

            action = cmdinfo[0]
            action_argc = cmdinfo[1]
            cmdargs = RE_CMDARGS.findall(c[1].strip())
            cmdargs_len = len(cmdargs)

            if cmdargs_len > 0 and action_argc == 0:
                raise CommandError(c_str + " - command takes no parameters!")
            elif (action_argc > 0 and (cmdargs_len == 0 or cmdargs_len % action_argc != 0)) \
                    or (action_argc == 1 and cmdargs_len > 1):
                raise CommandError(c_str + " - incorrect number of parameters!")

            if cmdargs_len > 0:
                cmdargs = [int(float(x)) for x in cmdargs]
                cmdargs = [cmdargs[i:i + action_argc] for i in range(0, cmdargs_len, action_argc)]
                for x in cmdargs:
                    c_str = "{} {}".format(cmdname, str(x).strip('[]'))
                    c_str = re.sub(r',', '', c_str)
                    action_stack.append((c_str, action, x))
            else:
                action_stack.append((c_str, action, None))

        self.poweroffthread.stop()
        counter = 1
        for cmd, a, args in action_stack:
            self.logger.info("{}: {}".format(counter, cmd))
            counter += 1
            if args:
                yield a(*args)
            else:
                yield a()

        self.setseparator(True)
        self.poweroffthread.restart()

    # // Utility commands

    class PowerOffThread(Thread):
        _cancelled = False
        _powerofftime = None

        def __init__(self, interval, getpower, setpower):
            Thread.__init__(self)
            self.interval = interval
            self.getpower = getpower
            self.setpower = setpower
            self.setDaemon(True)

        def stop(self):
            self._cancelled = True

        def restart(self):
            self._cancelled = False

        def run(self):
            self._powerofftime = time.time() + self.interval
            while True:
                while self._cancelled or not self.getpower():
                    time.sleep(1)
                    self._powerofftime = time.time() + self.interval
                if time.time() > self._powerofftime:
                    self.setpower(False)
                time.sleep(1)


class CommandError(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = str(msg)

    def __str__(self):
        return self.msg[0] + self.msg[1:]


class NotCalibratedError(CommandError):
    def __init__(self):
        CommandError.__init__(self, "Plotter is not calibrated!")


class ExecutionError(CommandError):
    def __init__(self):
        CommandError.__init__(self, "Execution stopped by user!")
