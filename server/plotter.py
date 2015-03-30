from mathextra import *
import RPi.GPIO as GPIO
from time import sleep


class NotCalibratedError(Exception):
    def __str__(self):
        return "Plotter is not calibrated!"


class BadCommandError(Exception):
    def __str__(self):
        return "Bad command!"

class SN74HC595:
        def __init__(self, data, clock, latch, count=1):
                self.data = data
                self.clock = clock
                self.latch = latch
                self.count = count
                self.t = 0
                GPIO.setup(data, GPIO.OUT)
                GPIO.setup(clock, GPIO.OUT)
                GPIO.setup(latch, GPIO.OUT)
                GPIO.output(latch, False)
                GPIO.output(clock, False)
                self.pin = list(range(count*8))
                for p in self.pin:
                        self.pin[p] = False
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
                        for ps in self.pin: #ps Pin State
                                output = str(int(ps)) + output
                        self.cmd(output)
                        return True

        def output(self, *states):
                if type(states[0]) is not list:
                     nope = ([[stetes[0], states[1]]])
                for out in states:
                     if out[0] >= self.count*8:
                         return False #pin out of range #todo state is not 0 or 1
                     self.pin[out[0]] = out[1]
                self.update()
                return True

class A4988:
    _direction = 1

    def __init__(self, directionpin, steppin, sleeppin, resetpin, ms3pin, ms2pin, ms1pin, enablepin, revdir=False, spr=200, ms=16):
        self.directionPin = directionpin
        self.stepPin = steppin
        self.sleepPin = sleeppin
        self.resetPin = resetpin
        self.ms3pin = ms3pin
        self.ms2pin = ms2pin
        self.ms1pin = ms1pin
        self.enablePin = enablepin
        self.revdir = revdir
        self.spr = spr
        self.ms = ms
        mode = {1: '000', 2: '100', 4: '010', 8: '110', 16: '111'}
        print(mode[ms])
        print ('ms1 '+ str(mode[ms][0]))
        print ('ms2 '+ str(mode[ms][1]))
        print ('ms3 '+ str(mode[ms][2]))

        GPIO.setup(self.directionPin, GPIO.OUT)
        GPIO.setup(self.stepPin, GPIO.OUT)
#        sf.output(1, 1)
        # GPIO.setup(self.enablePin, GPIO.OUT)
        # GPIO.setup(self.resetPin, GPIO.OUT)
        # GPIO.setup(self.sleepPin, GPIO.OUT)

    def power(self, status):
        # GPIO.output(self.enablePin, not status)
        # GPIO.output(self.resetPin, not status)
        # GPIO.output(self.sleepPin, status)
        return True

    def move(self, steps, speed):  # speed - revolution per second
        t = 1.0/(self.spr*self.ms*speed)/2
        for i in range(abs(steps)):
            GPIO.output(self.stepPin, True)
            sleep(t)
            GPIO.output(self.stepPin, False)
            sleep(t)
            
    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value
        if self.revdir: value = not value
        GPIO.output(self.directionPin, value)


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
            length = self.on
        else:
            length = self.off
        self.pwm.start(length)
        sleep(0.5)


class Plotter:
    m1, m2 = [0, 0], [76846, 0]
    spr = 200  # steps per revolution in full step mode
    ms = 16    # (1, 2, 4, 8, 16)
    length = (0, 0)
    calibrated = False
    right_engine, left_engine = None, None

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        print("Initializing shift register")
        self.sf = SN74HC595(15, 11, 13, 2)

        print("Initializing left engine...")
        self.left_engine = A4988(26, 24, 14, 13, 12, 11, 10, 9, True)
        self.left_engine.power(True)
        print("Initializing right engine...")
        self.right_engine = A4988(18, 16, 6, 5, 4, 3, 2, 1)
        self.right_engine.power(True)

        print("Initializing separator...")
        self.separator = Servo(23)

    def move_vertical(self, steps, speed):
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

    def move_horizontal(self, steps, speed):
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

    def move_both(self, left, right, speed):
        gleft = int(left)
        gright = int(right)
        if gleft == 0 or gright == 0:
            # move
            self.left_engine.move(gleft, float(speed))
            self.right_engine.move(gright, float(speed))
        else:
            rel = abs(float(gleft)/gright)
            # print(rel)
            done = 0
            ldir = sign(gleft)  # Left Direction
            rdir = sign(gright)  # Right Direction
            print(ldir)
            print(rdir)
            for i in range(1, abs(gright)+1):
                # print('R')
                self.right_engine.move(rdir, float(speed))
                htbd = int(i*rel)  # steps which Has To Be Done
                td = htbd - done  # steps To Do
                # print('L ' + str(td))
                self.left_engine.move(ldir*td, float(speed))
                done = htbd

    def goto(self, x, y, speed):
        if not self.calibrated:
            raise NotCalibratedError()
        #here will be some lines of code
    def calibrate(self, x, y):
        self.length = ctl((int(x), int(y)), self.m1, self.m2)
        self.calibrated = True

    def exec(self, command):
        part = command.split(' ')
        if part[0] == 'L' or part[0] == 'R':
            if part[0] == 'L':
                mot = self.left_engine
            else:
                mot = self.right_engine

            if sign(int(part[1])) == 1:
                mot.direction = 1
            else:
                mot.direction = 0

            mot.move(int(part[1]), float(part[2]))
        elif part[0] == 'V':
            self.move_vertical(int(part[1]), float(part[2]))
        elif part[0] == 'H':
            self.move_horizontal(int(part[1]), float(part[2]))
        elif part[0] == 'S':
            self.separator.set(int(part[1]))
        elif part[0] == 'P':
            sleep(float(part[1]))
        elif part[0] == 'B':
            self.move_both(int(part[1]), int(part[2]), float(part[3]))
        elif part[0] == 'C':
            self.calibrate(int(part[1]), int(part[2]))
            return self.length
        elif part[0] == 'COR':
            if self.calibrated:
                return ltc(len, self.m1, self.m2)
            else:
                raise NotCalibratedError()
        elif part[0] == 'LEN':
            return self.length
        elif part[0] == 'GOTO':  # Actually move to spec. position
            if self.calibrated:
                self.goto(part[1], part[2], part[3])
            else:
                raise NotCalibratedError()
        else:
            raise BadCommandError()
        return ""
