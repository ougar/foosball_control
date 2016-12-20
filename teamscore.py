#!/usr/bin/python
# coding: utf8

import time
import pigpio
import max7219bb
import threading
import logging

log = logging.getLogger(__name__)

class TeamScore:
  
  def __init__(self, pi, clock, data, load):
    self.leds=max7219bb.MAX7219bb(pi, clock, data, load)
    # Teamscore configuration variables
    self.setIntensity(4)      # Current intensity - default=4
    self.leading0=False       # Should leading zero be displayed
    # Teamscore status variables
    self.lastgoal=None        # Time of last goal
    self.active=False         # Current status - initially off
    self.lastcommand=0        # When something was last send to the leds
    self.ledstatus=True       # NOT USED - planned to be used when blnking leds
    # Control LED blinking
    self.blinknum=2           # Blink on score update (turn off) this many times. 0 or false to deactivate
    self.blinktime=.2         # Stay on and off for this many seconds
    self.blinklock=threading.Lock()
    self.blinkthread=None     # Thread object for last blinker thread started
    self.deadthreads=()       # List of threads asked to die, ready to be joined and thus erased
    # Default max7219 setup
    self.leds.setDecode(True) # Use decoding, so the digits are send as decimals
    self.leds.useDigits(2)    # Only scan 2 digits.
    self.reset()              # Start with a zero

  # Re-initialize leds. Sometimes stuff goes crazy, so reset to current setup
  # Send current score, and turn off/on depending on status
  # Moved to wakeup to reinit every time leds are turned on
  def reinit(self):
    pass

  def setLock(self, lock):
    self.leds.setLock(lock)

  def getLock(self):
    return(self.leds.lock)

  def setIntensity(self, intensity):
    self.intensity=intensity
    self.leds.intensity(intensity)

  def setLeading0(self, v=True):
    self.leading0=v
    self.setScore(self.score)

  def setBlink(blinknum=2, blinktime=0.2):
    self.blinknum=blinknum
    self.blnktime=blinktime

  def shutdown(self):
    self.leds.shutdown()
    self.active=False

  def wakeup(self):
    self.active=True
    self.leds.disableTest()           # Turn off test mode
    self.setIntensity(self.intensity) # Reset intensity to current value
    self.leds.setDecode(True)         # Use decimal decoding
    self.send()                       # Send current score
    self.leds.wakeup()

  def blinkOn(self):
    self.leds.wakeup()
    self.active=True
  
  def blinkOff(self):
    self.leds.shutdown()
    self.active=False

  def goal(self):
    self.setScore(self.score+1)
    self.blinkStart()

#  def goaldown(self): 
#    self.setScore(max(0,self.score-1))
#    self.blinkCancel()

  def scoreCorrect(self, newscore):
    self.setScore(newscore)
    self.blinkCancel()

  def reset(self):
    self.setScore(0)
    if self.active: self.blinkStart()

  def setScore(self,num):
    self.score=num
    self.send()

  def blinkCancel(self):
    try:
      self.blinkthread.stoprequest.set()
    except:
      pass
    with self.blinklock:
      if not self.active: self.wakeup()

  def blinkStart(self):
    self.blinkCancel()
    self.blinkthread=EffectThread(self)
    self.blinkthread.start()

  def send(self):
    d1=self.score%10
    d2=int(self.score/10)
    self.leds.send(1,d1)
    # Check if leading zero should be desplayed
    if d2==0 and not self.leading0: d2=15
    self.leds.send(2,d2)

class EffectThread(threading.Thread):

  def __init__(self, teamscore):
    super(EffectThread, self).__init__()
    self.teamscore=teamscore
    self.stoprequest=threading.Event()
    self.blinkCurrent=0
    self.blinkTarget=2*teamscore.blinknum
    self.blinkTime=teamscore.blinktime

  def stop(self):
    self.stoprequest.set()

  def run(self):
    while self.blinkCurrent<self.blinkTarget:
      time.sleep(self.blinkTime)
      with self.teamscore.blinklock:
        if self.stoprequest.isSet(): break
        if self.blinkCurrent%2==0: self.teamscore.blinkOff()
        else:                      self.teamscore.blinkOn()
        self.blinkCurrent+=1
  
class TeamScoreException(Exception): pass
