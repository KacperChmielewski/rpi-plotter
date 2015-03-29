enable = 1

import RPi.GPIO as GPIO
from time import sleep
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)



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
		self.pin = range(count*8)
                for p in self.pin:
                        self.pin[p] = False
        def cmd(self, cmd):
                for state in str(cmd):
                        GPIO.output(self.data, int(state))
                        GPIO.output(self.clock, True)
                        sleep(self.t)
			print 'elo'
                        GPIO.output(self.clock, False)
			sleep(self.t)
                GPIO.output(self.latch, True)
                sleep(self.t)
                GPIO.output(self.latch, False)

        def output(self, pin, state):
                if pin >= self.count*8:
                        return False
                else:
                        output = ''
                        self.pin[pin] = state
                        for ps in self.pin: #ps Pin State
                                output = str(int(ps)) + output
                        self.cmd(output)



sf = SN74HC595(15, 11, 13, 2)

sf.output(7, 0)

sf.output(8, 1) #fan

sf.output(1, enable) #enable
sf.output(2, 1) #ms1
sf.output(3, 1) #ms2
sf.output(4, 1) #ms3
sf.output(5, 1) #reset
sf.output(6, 1) #sleep

sf.output(9, enable) #enable
sf.output(10, 1) #ms1
sf.output(11, 1) #ms2
sf.output(12, 1) #ms3
sf.output(13, 1) #reset
sf.output(14, 1) #sleep

