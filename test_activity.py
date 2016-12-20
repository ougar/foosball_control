#!/usr/bin/python
# coding: utf-8

# Standard libraries
import time
import threading
import logging
import readchar

# My own standard libraries
import pigpio
import kdate
import button

# Foosball libraries
import teamscore
import goaldetect
import activity
import external

def ktime():
  return(time.strftime("%Y-%m-%d %H:%M:%S"))

def vacant():
  print "%s - Table vacant" % ktime()

def occupied():
  print "%s - Table occupied" % ktime()

pi=pigpio.pi()
activity=activity.Activity(pi, gpio=17, onVacant=vacant, onOccupied=occupied)
activity.start()

try: 
  print "Starting activity detector..."
  while True:
    time.sleep(1)

except KeyboardInterrupt:
  print "Keyboard interrupt"

finally:
  print "Running cleanup code"
  pi.stop()
