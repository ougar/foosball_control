#!/usr/bin/python
import pigpio
import time
import threading
import logging

# Fetch logger from main thread
log = logging.getLogger(__name__)

class GoalDetect:
  
  def __init__(self, pi, power, detect1, detect2, config=False, onGoal=None):
    self.pi=pi
    # Set power pin and turn lasers off
    log.debug("Assigning laser power pin=%d" % power)
    self.power=power
    self.pi.set_mode(power, pigpio.OUTPUT)
    self.pi.write(power,0)
    # Set detection pins and set up callbacks
    log.debug("Assigning laser detection pins=%d,%d" % (detect1, detect2))
    self.detect=(detect1, detect2)
    self.pi.set_mode(detect1,pigpio.INPUT)
    self.pi.set_mode(detect2,pigpio.INPUT)
    pi.set_pull_up_down(detect1, pigpio.PUD_UP)
    pi.set_pull_up_down(detect2, pigpio.PUD_UP)
    # Setting onGoal callback function
    if onGoal:
      log.debug("Setting onGoal callback to function '%s'" % onGoal.__name__)
    self.onGoal=onGoal
    self.cb1=False
    self.cb2=False

    # Disable goal output
    self.output=(False, False)
    # Detector not started
    self.active=False

  def start(self):
    log.debug("Starting goaldetector")
    # Turn on laser
    self.pi.write(self.power,1)
    # Sleep 1ms to allow lasers to turn on, so goaldetection isn't triggered
    time.sleep(.1)
    self.cb1 = self.pi.callback(self.detect[0], pigpio.EITHER_EDGE, self.goaltrigger)
    self.cb2 = self.pi.callback(self.detect[1], pigpio.EITHER_EDGE, self.goaltrigger)
    self.pi.set_glitch_filter(self.detect[0], 3000)
    self.pi.set_glitch_filter(self.detect[1], 3000)
    self.active=True

  def stop(self):
    log.debug("Stopping goaldetector")
    if self.cb1: self.cb1.cancel()
    if self.cb2: self.cb2.cancel()
    self.pi.set_glitch_filter(self.detect[0], 0)
    self.pi.set_glitch_filter(self.detect[1], 0)
    # Turn off laser
    self.pi.write(self.power,0)
    self.active=False

  def setOutput(self, team1, team2):
    log.debug("Setting goal-indicators to pins %d,%d" % (team1, team2))
    # Reset old pins (if they exist)
    for pin in self.output:
      if pin: self.pi.set_mode(pin, pigpio.INPUT)
    # Assign new pins
    self.output=(team1,team2)
    # Setup new pins
    for pin in self.output:
      if pin:
        self.pi.set_mode(pin, pigpio.OUTPUT)
        self.pi.write(pin, 0)
         
  def outputGoal(self, team):
    pin=self.output[team-1]
    # If pin is set, then set pin high
    if pin:
      # Signal a goal on the pin
      self.pi.write(pin,1)
      log.debug("Giving goal indication on pin %d",pin)
      # Set a timer to turn off the pin in 2 seconds
      treading.Timer(2.0, outputOff, [team])

  def outputOff(self, team):
    pin=self.output[team-1]
    if pin: 
      self.pi.write(pin,0)
      log.debug("Turning off  goal indication on pin %d",pin)

  def goaltrigger(self, gpio, level, tick):
    log.debug("Goal triggered on gpio=%d, level=%d" % (gpio,level))
    # If detector is not active, do nothing (callbacks should be inactive anyway)
    if not self.active: return
    # Only react to laser off events 
    # (laser off -> phototransistor off -> No connection to ground -> pin pulled high by pull-up)
    # Should perhaps be changed to measure ball passing time, to filter out
    # false positives
    if level==0: return
    # Which team scored
    if   gpio==self.detect[0]: team=1
    elif gpio==self.detect[1]: team=2
    else: raise GoalDetectException("Strange pin triggered in goaldetect")
    # Set output pin (if defined)
    self.outputGoal(team)
    # Call external callback function
    self.onGoal(team)
    
class GoalDetectException(Exception): pass
