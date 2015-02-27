from mathextra import *
import RPi.GPIO as GPIO
from time import sleep


class NotCalibratedException(Exception):
    def __str__(self):
        return "Plotter is not calibrated!"


class A4988:
    _direction = 1

    def __init__(self, steppin, directionpin, enablepin, resetpin, sleeppin, spr=200, ms=16):
        self.directionPin = directionpin
        self.stepPin = steppin
        self.enablePin = enablepin
        self.resetPin = resetpin
        self.sleepPin = sleeppin
        self.spr = spr
        self.ms = ms
        GPIO.setup(self.directionPin, GPIO.OUT)
        GPIO.setup(self.stepPin, GPIO.OUT)
        # GPIO.setup(self.enablePin, GPIO.OUT)
        # GPIO.setup(self.resetPin, GPIO.OUT)
        # GPIO.setup(self.sleepPin, GPIO.OUT)

    def power(self, status):
        # GPIO.output(self.enablePin, not status)
        # GPIO.output(self.resetPin, not status)
        # GPIO.output(self.sleepPin, status)
        sleep(1)
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
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        print("Initializing right engine...")
        self.right_engine = A4988(24, 23, 8, 7, 25)
        self.right_engine.power(True)
        print("Initializing left engine...")
        self.left_engine = A4988(7, 8, 23, 24, 25)
        self.left_engine.power(True)
        print("Initializing separator...")
        self.separator = Servo(14)

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

    def goto(self, x, y, speed):
        if not self.calibrated:
            raise NotCalibratedException()

        gleft = int(x)
        gright = int(y)
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
            for i in range(1, abs(gright)+1):
                # print('R')
                self.right_engine.move(rdir, float(speed))
                htbd = int(i*rel)  # steps which Has To Be Done
                td = htbd - done  # steps To Do
                # print('L ' + str(td))
                self.left_engine.move(ldir*td, float(speed))
                done = htbd

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
            self.move_vertical(part[1], part[2])
        elif part[0] == 'H':
            self.move_horizontal(part[1], part[2])
        elif part[0] == 'S':
            self.separator.set(int(part[1]))
        elif part[0] == 'P':
            sleep(float(part[1]))
        elif part[0] == 'C':
            self.calibrate(part[1], part[2])
            return self.length
        elif part[0] == 'COR':
            if self.calibrated:
                return ltc(len, self.m1, self.m2)
            else:
                return "not calibrated"
        elif part[0] == 'LEN':
            return self.length
        elif part[0] == 'GOTO':  # Actually move to spec. position
            if self.calibrated:
                self.goto(part[1], part[2], part[3])
            else:
                return "not calibrated"
        else:
            return 'bad command'
        return ""
