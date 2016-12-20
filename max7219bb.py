#!/usr/bin/python
# coding: utf8

import time
import pigpio
import logging
import threading

DECODE_MODE  = 0x09
INTENSITY    = 0x0a
SCAN_LIMIT   = 0x0b
SHUTDOWN     = 0x0c
DISPLAY_TEST = 0x0f

class MAX7219bb:
  
  def __init__(self, pi, clock, data, load, skipsetup=False, showcommand=False):
    self.pi=pi           # Pigpio instance
    # Define GPIO pins and set them to OUTPUT
    self.clock=clock     # Clock pin
    self.data=data       # Data-pin
    self.load=load       # Load pin (CS)
    pi.set_mode(clock, pigpio.OUTPUT)
    pi.set_mode(data,  pigpio.OUTPUT)
    pi.set_mode(load,  pigpio.OUTPUT)
    # Lock which ensures only 1 thread will try to send data to the max7219
    # If lock is supplied, reuse that lock. Necessary if several max chips share gpio pins
    self.lock=threading.Lock()
    # Should the commands sent to the max by printed
    self.showcommand=showcommand
    # Unless user asks for no setup, set max to sensible default state
    if not skipsetup:
      self.shutdown()            # Start in shutdown mode
      self.send(DISPLAY_TEST, 0) # Disable test mode
      self.useDigits(8)          # Scan all elements by default
      self.intensity(3)          # Set low intensity by default
      self.setDecode(False)      # Don't use any decode mode

  def setLock(self,lock):
    self.lock=lock

  def sendBits(self, value):
    #print "Value: %d" % value
    for i in range(0,16):
      mask=1 << (15-i)  # Calculate bit mask - select i'th bit
      q = (mask & value)>0
      #print "%d - %d - %d" % (i,mask,q)
      self.pi.write(self.clock,0)
      self.pi.write(self.data,q)
      self.pi.write(self.clock,1)

  def send(self, reg, data):
    if self.showcommand: self.showcom(reg, data)
    #print "%d - %d" % (reg,data)
    self.isInterval(reg,0,15)
    self.isInterval(data,0,255)
    # Make sure only 1 thread at a time sends stuff to the max7219.
    # Share the lock to make the lock protect several max-chips sharing data and clock pins
    with self.lock:
      self.pi.write(self.load,0)
      self.sendBits((reg << 8) + data)
      self.pi.write(self.load,1)

  def showcom(self,reg,data):
    if not self.showcommand: return
    if   reg==DECODE_MODE:  q="Decode"
    elif reg==INTENSITY:    q="Intensity"
    elif reg==SCAN_LIMIT:   q="Scan limit"
    elif reg==SHUTDOWN:     q="Shutdown"
    elif reg==DISPLAY_TEST: q="Display test"
    elif reg==0:            q="No-Op"
    elif reg>=1 and reg<=8: q="Digit %d" % reg
    else:                   q="???"
    print "%s: %d" % (q, data)

  def wakeup(self):
    self.send(SHUTDOWN, 1)

  def shutdown(self):
    self.send(SHUTDOWN, 0)

  def disableTest(self):
    self.send(DISPLAY_TEST, 0)

  # Use same decode mode for all digits. I cant see a situation where you need different decode modes :-)
  def setDecode(self,value=True):
    if value==True: self.decode=True
    else: self.decode=False
    self.send(DECODE_MODE, 255*(self.decode))

  def useDigits(self,n):
    self.isInterval(n,1,8)
    self.digits=n
    self.send(SCAN_LIMIT, n-1)

  def intensity(self, value):
    self.isInterval(value,0,15)
    self.send(INTENSITY, value)

  def clear(self):
    if self.decode: v=15
    else: v=0
    for i in range(1,self.digits+1):
      self.send(i,v)

  def isInt(self,value):
    try: return(value==int(value))
    except: return False

  def isInterval(self, value, minvalue, maxvalue):
    if self.isInt(value) and value>=minvalue and value<=maxvalue: return(True)
    else: raise Max7219Exception("Invalid value: %s - must be in interval %d-%d"      % (value, minvalue, maxvalue))

  # Convert from digital numbers to binary segments either flipped or not flipped
  def bitNumber(self, num, flip=False):
    bittable = ((126,126),(48,6),(109,109),(121,79),(51,23),(91,91),(95,123),(112,70),(127,127),(123,95))
    return(bittable[num][flip])

class Max7219Exception(Exception): pass
