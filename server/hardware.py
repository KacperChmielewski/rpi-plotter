from time import sleep

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Not RPi device, using fake GPIO instead...")
    import fakeGPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

length = [0, 0]


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
            raise EngineSpeedError("'speed' cannot be negative")
        elif speed == 0:
            raise EngineSpeedError("'speed' cannot be zero (moving without speed?)")

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
        self.pwmfactor = (on - off) / 100
        self.pwm.start(off)
        self.state = 0
        self.set(1)

    def set(self, status):
        if self.state == status:
            return True
        if status:
            for i in range(100):
                self.pwm.start(i * self.pwmfactor + self.off)
                sleep(0.01)
        else:
            for i in range(100):
                self.pwm.start(i * self.pwmfactor * -1 + self.on)
                sleep(0.01)
        self.state = status

class EngineSpeedError(Exception):
    def __init__(self, speed):
        self.speed = speed

    def __str__(self):
        if self.speed < 0:
            return "'speed' cannot be negative"
        elif self.speed == 0:
            return "'speed' cannot be zero (move without speed?)"
