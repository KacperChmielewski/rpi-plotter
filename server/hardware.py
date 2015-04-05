from mathextra import *
from time import sleep

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
    def __init__(self, pin, on=11, off=5):
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)

        self.pwm = GPIO.PWM(pin, 100)
        self.on = on
        self.off = off
        self.pwm.start(off)
        self.set(1)

    def set(self, status):
        if status:
            extend = self.on
        else:
            extend = self.off
        self.pwm.start(extend)
        sleep(0.5)


class Plotter:
    m1, m2 = [0, 0], [52861, 1337]
    spr = 200  # steps per revolution in full step mode
    ms = 16  # (1, 2, 4, 8, 16)
    calibrated = False
    right_engine, left_engine = None, None
    _power, _debug = False, False

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
        self.commands = {
            'L': self.moveleft,
            'R': self.moveright,
            'V': self.movevertical,
            'H': self.movehorizontal,
            'B': self.moveboth,
            'GOTO': self.goto,
            'P': self.pause,
            'S': self.setseparator,
            'C': self.calibrate,
            'COR': self.getcoord,
            'LEN': self.getlength,
            'POWER': self.setpower,
            'DEBUG': self.setdebug  # only in terminal
            # 'E': self.poweroff
        }

    @staticmethod
    def move(motor, steps, speed):
        steps = int(steps)
        speed = float(speed)
        if sign(steps) == 1:
            motor.direction = 1
        else:
            motor.direction = 0
        motor.move(steps, speed)

    def moveleft(self, steps, speed):
        self.move(self.left_engine, steps, speed)

    def moveright(self, steps, speed):
        self.move(self.right_engine, steps, speed)

    def movevertical(self, steps, speed):
        if sign(steps) == 1:
            self.left_engine.direction = 1
            self.right_engine.direction = 1
        else:
            self.left_engine.direction = 0
            self.right_engine.direction = 0

        speed *= 2
        for i in range(abs(int(steps))):
            self.left_engine.move(1, speed)
            self.right_engine.move(1, speed)

    def movehorizontal(self, steps, speed):
        if sign(steps) == 1:
            self.left_engine.direction = 1
            self.right_engine.direction = 0
        else:
            self.left_engine.direction = 0
            self.right_engine.direction = 1

        speed *= 2
        for i in range(abs(int(steps))):
            self.left_engine.move(1, speed)
            self.right_engine.move(1, speed)

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
                self.right_engine.move(1, float(speed))
                htbd = int(i * rel)  # steps which Has To Be Done
                td = htbd - done  # steps To Do
                self.left_engine.move(td, float(speed))
                done = htbd

    def goto(self, x, y, speed):
        if not self.calibrated:
            raise NotCalibratedError()
        else:
            destination = ctl((int(x), int(y)), self.m1, self.m2)
            if self.getdebug():
                print("Destination: " + destination)
            change = (int(destination[0] - length[0]), int(destination[1] - length[1]))
            if self.getdebug():
                print("Change: " + str(change))
            self.moveboth(change[0], change[1], speed)

    @staticmethod
    def pause(ms):
        sleep(int(ms))

    def setseparator(self, state):
        self.separator.set(bool(state))

    def calibrate(self, x, y):
        global length
        length = ctl((int(x), int(y)), self.m1, self.m2)
        length = [int(length[0]), int(length[1])]
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
        self._power = bool(int(value))

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
        self._debug = bool(int(value))
        state = "disabled"
        if self.getdebug():
            state = "enabled"
        print("Debug mode " + state)

    def execute(self, command):
        cmdparts = command.upper().split(' ')
        command = cmdparts[0].strip()
        commandargs = cmdparts[1:]
        action = self.commands.get(command)
        if not action:
            raise CommandError(command + " - bad command!")
        else:
            try:
                return action(*commandargs)
            except TypeError as ex:
                ex_msg = str(ex)

                if all(x in ex_msg for x in ['takes', 'positional argument', 'given']):  # too many argument(s)
                    raise CommandError("Too many arguments!")
                elif all(x in ex_msg for x in ['missing', 'required positional argument']):  # missing argument(s)
                    missing = ex_msg.rsplit(':', 1)[1].strip()
                    raise CommandError("Missing arguments: " + missing)
