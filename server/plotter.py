from threading import Thread
import re
import time

from mathextra import *
import hardware as hw


class Plotter:
    m1, m2 = [0, 0], [81013, 0]
    spr = 200  # steps per revolution in full step mode
    ms = 16  # (1, 2, 4, 8, 16)
    calibrated = False
    right_engine, left_engine = None, None
    _power, _debug = False, False
    startpoint, controlpoint = None, None
    _execpause, _execstop = False, False
    calibrationpoint = None

    def __init__(self, power=True, debug=False):
        self.setdebug(debug)
        if self.getdebug():
            print("Initializing shift register...")
        self.sr = hw.ShiftRegister(15, 11, 13, 2)

        if self.getdebug():
            print("Initializing ATX power supply...")
        self.atxpower = hw.ATX(7, 15, self.sr)

        if self.getdebug():
            print("Initializing left engine...")
        self.left_engine = hw.A4988(26, 24, 14, 13, 12, 11, 10, 9, self.sr, side=0, revdir=True)
        if self.getdebug():
            print("Initializing right engine...")
        self.right_engine = hw.A4988(18, 16, 6, 5, 4, 3, 2, 1, self.sr, side=1)

        if self.getdebug():
            print("Initializing separator...")
        self.separator = hw.Servo(23)

        self.setpower(power)

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
                           'Q': (self.qcurveto, 4),
                           'q': (self.qcurveto_rel, 4),
                           'T': (self.sqcurveto, 2),
                           't': (self.sqcurveto_rel, 2),
                           # TODO: elliptical arc command

                           # Plotter
                           'SLP': (time.sleep, 1),
                           'SEP': (self.setseparator, 1),
                           'CAL': (self.calibrate, 2),
                           'COR': (self.getcoord, 0),
                           'LEN': (self.getlength, 0),
                           'PWR': (self.setpower, 1),
                           'DBG': (self.setdebug, 1)  # prints info in terminal
                           # 'E': self.poweroff
        }
        self.poweroffthread = self.PowerOffThread(15, self.getpower, self.setpower)
        self.poweroffthread.start()

    def move(self, left, right, speed):
        if not self.getpower():
            self.setpower(True)
        gleft = int(left)
        gright = int(right)
        if gleft == 0 or gright == 0:
            # move
            self.left_engine.move(gleft, float(speed))
            self.right_engine.move(gright, float(speed))
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
                self.right_engine.move(1, float(speed))
                htbd = int(i * rel)  # steps which Has To Be Done
                td = htbd - done  # steps To Do
                self.left_engine.move(td, float(speed))
                done = htbd

    def moveto(self, x, y, speed=1, sep=True, savepoint=True):
        if not self.calibrated:
            raise NotCalibratedError()
        x += self.calibrationpoint[0]
        y += self.calibrationpoint[1]
        if not self.startpoint:
            self._savestartpoint()
        if self.controlpoint:
            self.controlpoint = None
        self.setseparator(sep)
        destination = ctl([int(x), int(y)], self.m1, self.m2)
        if self.getdebug():
            print("Destination: " + str(destination))
        change = (int(destination[0] - hw.length[0]), int(destination[1] - hw.length[1]))
        if self.getdebug():
            print("Strings change: " + str(change))
        self.move(change[0], change[1], speed)
        if savepoint:
            self._savestartpoint()

    def moveto_rel(self, x, y, speed=1, sep=True, savepoint=True):
        if not self.calibrated:
            raise NotCalibratedError()
        self.setseparator(sep)
        currentpos = self.getcoord(False)
        if not self.startpoint:
            self.startpoint = currentpos
        if self.controlpoint:
            self.controlpoint = None
        destination = ctl([currentpos[0] + int(x), currentpos[1] + int(y)], self.m1, self.m2)
        if self.getdebug():
            print("Destination: " + str(destination))
        change = (int(destination[0] - hw.length[0]), int(destination[1] - hw.length[1]))
        if self.getdebug():
            print("Strings change: " + str(change))
        self.move(change[0], change[1], speed)
        if savepoint:
            self._savestartpoint()

    def lineto(self, x, y, speed=1):
        self.moveto(x, y, speed, False, False)

    def lineto_rel(self, x, y, speed=1):
        self.moveto_rel(x, y, speed, False, False)

    def vertical(self, y, speed=1):
        self.moveto(int(self.getcoord()[0]), y, speed, False, False)

    def vertical_rel(self, y, speed=1):
        self.moveto_rel(0, y, speed, False, False)

    def horizontal(self, x, speed=1):
        self.moveto(x, int(self.getcoord()[1]), speed, False, False)

    def horizontal_rel(self, x, speed=1):
        self.moveto_rel(x, 0, speed, False, False)

    def closepath(self, speed=1):
        self.moveto(self.startpoint[0], self.startpoint[1], speed, False, False)

    def curveto(self, x1, y1, x2, y2, x, y, res=100):
        start = self.getcoord()
        for t in range(1, res + 1):
            bx = int(cubicbezier(t / res, start[0], x1, x2, x))
            by = int(cubicbezier(t / res, start[1], y1, y2, y))
            self.lineto(bx, by)
            self.controlpoint = (x2, y2)

    def curveto_rel(self, x1, y1, x2, y2, x, y, res=100):
        start = self.getcoord()
        for t in range(1, res + 1):
            bx = int(cubicbezier(t / res, 0, x1, x2, x))
            by = int(cubicbezier(t / res, 0, y1, y2, y))
            bx += start[0]
            by += start[1]
            self.lineto(bx, by)
            self.controlpoint = (x2 + start[0], y2 + start[1])

    def scurveto(self, x2, y2, x, y, res=100):
        x1, y1 = self._getconpointreflection()
        self.curveto(x1, y1, x2, y2, x, y, res)

    def scurveto_rel(self, x2, y2, x, y, res=100):
        start = self.getcoord()
        sx = start[0]
        sy = start[1]
        x1, y1 = self._getconpointreflection()
        self.curveto(x1, y1, x2 + sx, y2 + sy, x + sx, y + sy, res)

    def qcurveto(self, x1, y1, x, y, res=100):
        start = self.getcoord()
        for t in range(1, res + 1):
            bx = int(quadbezier(t / res, start[0], x1, x))
            by = int(quadbezier(t / res, start[1], y1, y))
            self.lineto(bx, by)
            self.controlpoint = (x1 + start[0], y1 + start[1])

    def qcurveto_rel(self, x1, y1, x, y, res=100):
        start = self.getcoord()
        for t in range(1, res + 1):
            bx = int(quadbezier(t / res, 0, x1, x))
            by = int(quadbezier(t / res, 0, y1, y))
            bx += start[0]
            by += start[1]
            self.lineto(bx, by)
            self.controlpoint = (x1 + start[0], y1 + start[1])

    def sqcurveto(self, x, y, res=100):
        x1, y1 = self._getconpointreflection()
        self.qcurveto(x1, y1, x, y, res)

    def sqcurveto_rel(self, x, y, res=100):
        start = self.getcoord()
        x1, y1 = self._getconpointreflection()
        self.qcurveto(x1, y1, x + start[0], y + start[1], res)

    def setseparator(self, state):
        self.separator.set(int(state))

    def calibrate(self, x, y):
        hw.length = ctl((int(x), int(y)), self.m1, self.m2)
        hw.length = [int(hw.length[0]), int(hw.length[1])]
        self.calibrationpoint = (x, y)
        self.calibrated = True

    def getcoord(self, offset=True):
        if self.calibrated:
            x, y = ltc(hw.length, self.m1, self.m2)
            if offset:
                return x - self.calibrationpoint[0], y - self.calibrationpoint[1]
            else:
                return x, y
        else:
            raise NotCalibratedError()

    @staticmethod
    def getlength():
        return hw.length

    def getpower(self):
        return self._power

    def setpower(self, value):
        value = bool(int(value))
        if self._power == value:
            if self.getdebug():
                state = "OFF"
                if value:
                    state = "ON"
                print("POWER: already turned " + state)
            return
        self._power = value

        if self.getdebug():
            state = "OFF"
            if self.getpower():
                state = "ON"
            print("Turning {} power and motors...".format(state))
        self.atxpower.power(self.getpower())
        self.atxpower.loadr(self.getpower())
        self.left_engine.power(self.getpower())
        self.right_engine.power(self.getpower())

    def getdebug(self):
        return self._debug

    def setdebug(self, value):
        value = bool(int(value))
        if self._debug == value:
            return
        self._debug = value

        state = "disabled"
        if self.getdebug():
            state = "enabled"
        print("Debug mode " + state)

    def getexecpause(self):
        return self._execpause

    def setexecpause(self, value):
        value = bool(int(value))
        if self._execpause == value:
            return
        self._execpause = value

        if self.getdebug():
            if value:
                print("Paused")
            else:
                print("Unpaused")

    def stopexecute(self):
        self._execstop = True

    def _savestartpoint(self):
        self.startpoint = self.getcoord()

    def _getconpointreflection(self):
        current = self.getcoord()
        x = current[0] + (current[0] - self.controlpoint[0])
        y = current[1] + (current[1] - self.controlpoint[1])
        return x, y

    def execute(self, command):
        """:type command: str"""
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

        cmdlist = re.findall(r'([A-Za-z]+)\s*((?:-?(\d((E|e)(\+|\-)\d+)?)*\.?(?:\s|,)*)*)',
                             command)

        if not cmdlist:
            raise CommandError(command + " - syntax error!")

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
            cmdargs = re.findall(r'[\+\-\w\.]+', c[1].strip())
            cmdargs_len = len(cmdargs)

            if cmdargs_len > 0 and action_argc == 0:
                raise CommandError(c_str + " - command takes no parameters!")
            elif (action_argc > 0 and (cmdargs_len == 0 or cmdargs_len % action_argc != 0)) \
                    or (action_argc == 1 and cmdargs_len > 1):
                raise CommandError(c_str + " - incorrect number of parameters!")

            self.poweroffthread.stop()
            if cmdargs_len > 0:
                cmdargs = [int(float(x)) for x in cmdargs]
                cmdargs = [cmdargs[i:i + action_argc] for i in range(0, cmdargs_len, action_argc)]
                for x in cmdargs:
                    yield action(*x)
            else:
                yield action()
            self.setseparator(True)
            self.poweroffthread.restart()

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

    def __str__(self, capital=True):
        if capital:
            return self.msg[0].upper() + self.msg[1:]
        else:
            return self.msg[0].lower() + self.msg[1:]


class NotCalibratedError(CommandError):
    def __init__(self):
        CommandError.__init__(self, "Plotter is not calibrated!")


class ExecutionError(CommandError):
    def __init__(self):
        CommandError.__init__(self, "Execution stopped by user!")
