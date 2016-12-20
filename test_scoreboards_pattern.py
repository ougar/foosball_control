#!/usr/bin/python
# coding: utf8

import max7219bb
import time
import pigpio

pi=pigpio.pi()
m=max7219bb.MAX7219bb(pi, clock=22, data=27, load=23)
m.clear()
m.wakeup()

pattern_updown=((64,34,20,8,20,34))
pattern_leftright=((6,48,0,0),(0,0,6,48))
pattern_spin=((64,0,0,0,0,0,0,8,4,2),(0,0,64,32,16,8,0,0,0,0))

pp=pattern_spin
try:
  m.send(1,m.bitNumber(0))
  m.send(2,m.bitNumber(1))
  time.sleep(2)
  m.send(1,m.bitNumber(1))
  m.send(2,m.bitNumber(1))

  time.sleep(.4)
  m.shutdown()
  time.sleep(.2)
  m.wakeup()

  time.sleep(.2)
  m.shutdown()
  time.sleep(.2)
  m.wakeup()
  time.sleep(.3)

  for q in range(1,3):
    for i in range(0,len(pp[1])):
      d1=pp[0][i]
      d2=pp[-1][i]
      m.send(1,d2)
      m.send(2,d1)
      time.sleep(.01)

  m.send(1,m.bitNumber(1))
  m.send(2,m.bitNumber(1))

  time.sleep(.2)
  m.shutdown()
  time.sleep(.2)
  m.wakeup()

  time.sleep(.2)
  m.shutdown()
  time.sleep(.2)
  m.wakeup()

except KeyboardInterrupt:
  print("Keyboard interrupt")

finally:
  print("Running finally cleanup code")
  pi.stop

