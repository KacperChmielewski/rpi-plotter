from mathextra import *
from time import sleep
import re

try:
    import RPi.GPIO as GPIO
except ImportError:
    import fakeGPIO as GPIO

length = [0, 0]


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


class ShiftRegister:
    t = 0

    def __init__(self, data, clock, latch, count=1):
        self.data = data
        self.clock = clock
        self.latch = latch
        self.count = count
        GPIO.setup(data, GPIO.OUT)
        GPIO.setup(clock, GPIO.OUT)
        GPIO.setup(latch, GPIO.OUT)
        GPIO.output(latch, False)
        GPIO.output(clock, False)
        self.pin = [False] * (count * 8)

    def cmd(self, cmd):
        for state in str(cmd):
            GPIO.output(self.data, int(state))
            GPIO.output(self.clock, True)
            sleep(self.t)
            GPIO.output(self.clock, False)
            sleep(self.t)
        GPIO.output(self.latch, True)
        sleep(self.t)
        GPIO.output(self.latch, False)

    def state(self, pin):
        return self.pin[pin]

    def update(self):
        output = ''
        for ps in self.pin:  # ps pin State
            output = str(int(ps)) + output
        self.cmd(output)
        return True

    def output(self, *states):
        if type(states[0]) is not list:
            states = ([[states[0], states[1]]])
        for out in states:
            if out[0] >= self.count * 8:
                # TODO: state is not 0 or 1
                return False  # pin out of range
            self.pin[out[0]] = out[1]
        self.update()
        return True


class ATX:
    def __init__(self, highcurrent, load, sr):
        self.highcurrent = highcurrent
        self.load = load
        self.sr = sr
        sr.output([highcurrent, 0], [load, 0])

    def power(self, status):
        self.sr.output(self.highcurrent, status)
        return True

    def loadr(self, status):
        self.sr.output(self.load, status)
        return True


class A4988:
    _direction = 1

    def __init__(self, directionpin, steppin, sleeppin, resetpin, ms3pin, ms2pin, ms1pin, enablepin, sr,
                 ms=16, spr=200, **kwargs):
        self.directionpin = directionpin
        self.steppin = steppin
        self.sleeppin = sleeppin
        self.resetpin = resetpin
        self.ms3pin = ms3pin
        self.ms2pin = ms2pin
        self.ms1pin = ms1pin
        self.enablepin = enablepin
        self.ms = ms
        self.spr = spr
        self.sr = sr
        self.revdir = kwargs.get('revdir', False)
        self.side = kwargs.get('side', 0)
        # disable A4988 before setup
        self.sr.output([enablepin, 1], [resetpin, 0], [sleeppin, 0])

        # setting up MS
        mode = {1: '000', 2: '100', 4: '010', 8: '110', 16: '111'}
        self.sr.output([ms1pin, mode[ms][0]], [ms2pin, mode[ms][1]], [ms3pin, mode[ms][2]])

        # setting up GPIO outputs for direction and step 
        GPIO.setup(self.directionpin, GPIO.OUT)
        GPIO.setup(self.steppin, GPIO.OUT)

    def power(self, status):
        self.sr.output([self.enablepin, not status], [self.resetpin, status], [self.sleeppin, status])
        sleep(0.01)
        return True

    def move(self, steps, speed):  # speed - revolutions per second
        if speed < 0:
            raise CommandError("'speed' cannot be negative")
        elif speed == 0:
            raise CommandError("'speed' cannot be zero (moving without speed?)")

        # interval
        t = 1.0 / (self.spr * self.ms * speed) / 2

        # length update
        steps = abs(steps)
        if self._direction == 0:
            steps *= -1
        length[self.side] += steps

        for i in range(abs(steps)):
            GPIO.output(self.steppin, True)
            sleep(t)
            GPIO.output(self.steppin, False)
            sleep(t)

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value
        if self.revdir:
            value = not value
        GPIO.output(self.directionpin, value)


class Servo:
    def __init__(self, pin, on=6.3, off=2.5):
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)

        self.pwm = GPIO.PWM(pin, 50)
        self.on = on
        self.off = off
        self.pwmfactor = (on-off)/100
        self.pwm.start(off)
        self.state = 0
        self.set(1)

    def set(self, status):
        if self.state == status:
            return True
        if status:
            for i in range(100):
                self.pwm.start(i*self.pwmfactor+self.off)
                sleep(0.01)
        else:
            for i in range(100):
                self.pwm.start(i*self.pwmfactor*-1+self.on)
                sleep(0.01)
        self.state = status


class Plotter:
    m1, m2 = [0, 0], [81013, 0]
    spr = 200  # steps per revolution in full step mode
    ms = 16  # (1, 2, 4, 8, 16)
    calibrated = False
    right_engine, left_engine = None, None
    _power, _debug, _preview = False, False, False
    beginpoint, controlpoint = None, None
    _execpause, _execstop = False, False
    calibrationpoint = None

    def __init__(self, power=True, debug=False):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        self.setdebug(debug)
        if self.getdebug():
            print("Initializing shift register...")
        self.sr = ShiftRegister(15, 11, 13, 2)

        if self.getdebug():
            print("Initializing ATX power supply...")
        self.atxpower = ATX(7, 15, self.sr)

        if self.getdebug():
            print("Initializing left engine...")
        self.left_engine = A4988(26, 24, 14, 13, 12, 11, 10, 9, self.sr, side=0, revdir=True)
        if self.getdebug():
            print("Initializing right engine...")
        self.right_engine = A4988(18, 16, 6, 5, 4, 3, 2, 1, self.sr, side=1)

        if self.getdebug():
            print("Initializing separator...")
        self.separator = Servo(23)

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
            'SLP': (sleep, 1),
            'SEP': (self.setseparator, 1),
            'CAL': (self.calibrate, 2),
            'COR': (self.getcoord, 0),
            'LEN': (self.getlength, 0),
            'PWR': (self.setpower, 1),
            'DBG': (self.setdebug, 1),  # prints info in terminal
            'PRV': (self.setpreview, 1)
            # 'E': self.poweroff
        }

    def moveboth(self, left, right, speed):
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
                    sleep(0.1)
                self.right_engine.move(1, float(speed))
                htbd = int(i * rel)  # steps which Has To Be Done
                td = htbd - done  # steps To Do
                self.left_engine.move(td, float(speed))
                done = htbd

    def moveto(self, x, y, speed=1, sep=True, savepoint=True):
        if not self.calibrated:
            raise NotCalibratedError()
        if not self.beginpoint:
            currentpos = ltc(length, self.m1, self.m2)
            self.beginpoint = currentpos
        x += self.calibrationpoint[0]
        y += self.calibrationpoint[1]
        self.setseparator(sep)
        destination = ctl([int(x), int(y)], self.m1, self.m2)
        if self.getdebug():
            print("Destination: " + str(destination))
        change = (int(destination[0] - length[0]), int(destination[1] - length[1]))
        if self.getdebug():
            print("Change: " + str(change))
        self.moveboth(change[0], change[1], speed)
        if savepoint:
            currentpos = ltc(length, self.m1, self.m2)
            self.beginpoint = currentpos

    def moveto_rel(self, x, y, speed=1, sep=True, savepoint=True):
        if not self.calibrated:
            raise NotCalibratedError()
        self.setseparator(sep)
        currentpos = ltc(length, self.m1, self.m2)
        if not self.beginpoint:
            self.beginpoint = currentpos
        destination = ctl([currentpos[0] + int(x), currentpos[1] + int(y)], self.m1, self.m2)
        if self.getdebug():
            print("Destination: " + str(destination))
        change = (int(destination[0] - length[0]), int(destination[1] - length[1]))
        if self.getdebug():
            print("Change: " + str(change))
        self.moveboth(change[0], change[1], speed)
        if savepoint:
            currentpos = ltc(length, self.m1, self.m2)
            self.beginpoint = currentpos

    def lineto(self, x, y, speed=1):
        self.moveto(x, y, speed, False, False)

    def lineto_rel(self, x, y, speed=1):
        self.moveto_rel(x, y, speed, False, False)

    def vertical(self, y, speed=1):
        self.moveto(length[0], y, speed, False, False)

    def vertical_rel(self, y, speed=1):
        self.moveto_rel(0, y, speed, False, False)

    def horizontal(self, x, speed=1):
        self.moveto(x, length[1], speed, False, False)

    def horizontal_rel(self, x, speed=1):
        self.moveto_rel(x, 0, speed, False, False)

    def closepath(self, speed=1):
        self.moveto(self.beginpoint[0], self.beginpoint[1], speed, True, False)

    def curveto(self, x1, y1, x2, y2, x, y, res=100):
        start = ltc(length, self.m1, self.m2)
        for t in range(0, res):
            bx = cubicbezier(t / res, start[0], x1, x2, x) / 25
            by = cubicbezier(t / res, start[1], y1, y2, y) / 25
            self.lineto(bx, by)

    def curveto_rel(self, x1, y1, x2, y2, x, y, res=100):
        for t in range(0, res):
            bx = cubicbezier(t / res, 0, x1, x2, x) / 25
            by = cubicbezier(t / res, 0, y1, y2, y) / 25
            self.lineto_rel(bx, by)

    def scurveto(self, x2, y2, x, y, res=100):
        raise NotImplementedError()

    def scurveto_rel(self, x2, y2, x, y, res=100):
        raise NotImplementedError()

    def qcurveto(self, x1, y1, x, y, res=100):
        start = ltc(length, self.m1, self.m2)
        for t in range(0, res):
            bx = quadbezier(t / res, start[0], x1, x) / 25
            by = quadbezier(t / res, start[1], y1, y) / 25
            self.lineto(bx, by)

    def qcurveto_rel(self, x1, y1, x, y, res=100):
        for t in range(0, res):
            bx = quadbezier(t / res, 0, x1, x) / 25
            by = quadbezier(t / res, 0, y1, y) / 25
            self.lineto_rel(bx, by)

    def sqcurveto(self, x, y, res=100):
        raise NotImplementedError()

    def sqcurveto_rel(self, x, y, res=100):
        raise NotImplementedError()

    def setseparator(self, state):
        self.separator.set(int(state))

    def calibrate(self, x, y):
        global length
        length = ctl((int(x), int(y)), self.m1, self.m2)
        length = [int(length[0]), int(length[1])]
        self.calibrationpoint = (x, y)
        self.calibrated = True

    def getcoord(self):
        if self.calibrated:
            return ltc(length, self.m1, self.m2)
        else:
            raise NotCalibratedError()

    @staticmethod
    def getlength():
        return length

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

    def getpreview(self):
        return self._preview

    def setpreview(self, value):
        value = bool(int(value))
        if self._preview == value:
            return
        self._preview = value

        state = "disabled"
        if self.getdebug():
            if self.getpreview():
                state = "enabled"
            print("Preview " + state)

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

    def execute(self, command):
        if not re.match(r'^\s*[A-Za-z]', command):
            if len(command) < 15:
                formatlen = len(command)
            else:
                formatlen = 15

        # cmdlist = re.findall(r'([A-Za-z]+)\s*((?:-?\d*\.?\d+(?:\s|,)*)*)', command)
        cmdlist = re.findall(r'([A-Za-z]+)\s*((?:-?(\d((E|e)(\+|\-)\d+)?)*\.?(\d((E|e)(\+|\-)\d+)?)+(?:\s|,)*)*)', command)

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
            if cmdargs_len > 0:
                cmdargs = [int(float(x)) for x in cmdargs]
                cmdargs = [cmdargs[i:i+action_argc] for i in range(0, cmdargs_len, action_argc)]
                for x in cmdargs:
                    yield action(*x)
            else:
                yield action()
