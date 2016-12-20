#!/usr/bin/python
# coding: utf8

import pigpio
import time
import button
import teamscore
import math
import logging

logging.basicConfig(level=logging.DEBUG,format='%(levelname)s:%(threadName)s:%(message)s')

last=0
# Create a pigpio object and a max7219 object
pi=pigpio.pi()
score=teamscore.TeamScore(pi, clock=22, data=27, load=23)

score.wakeup()
value=0

# Test callback function
def test(gpio, level, tick, butnum):
  global last, score, value
  if level==1: 
    state="released"
  else: 
    state="pushed  "
    if butnum==1: value+=1
    else: value-=1
    value=value%100
    score.scoreCorrect(value)
  s=tick-last
  last=tick
  print "Button %d %s at tick: %d (ellapsed: %d). Newvalue %d" % (butnum, state, tick, s, value)

# Create 2 buttons
a = button.Button(pi=pi, gpio=25, callback=test, args=[1])
b = button.Button(pi=pi, gpio=18, callback=test, args=[2])

# Start an infinite loop, and wait for button events
print "Starting main loop"
try:
  while True:
    time.sleep(1)

except KeyboardInterrupt:
  print("Keyboard interrupt")

finally:
  print("Running finally cleanup code")
  pi.stop

