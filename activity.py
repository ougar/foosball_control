#!/usr/bin/python
# coding: utf8

import pigpio
import time
import kdate
import logging
import threading
import os
import ctypes
#import docopt
#import sys
#import subprocess

log = logging.getLogger("Foosball")

class Activity:

  def __init__(self, pi, gpio, power=False, config=False, onVacant=None, onOccupied=None):
    self.pi=pi
    self.gpio=gpio
    self.gpio_power=power
    # Setup
    self.pi.set_mode(self.gpio, pigpio.INPUT)
    self.pi.set_pull_up_down(self.gpio, pigpio.PUD_DOWN)
    if self.gpio_power:  # If power-gpio supplied, then set it up and turn off
      self.pi.set_mode(self.gpio_power, pigpio.OUTPUT)
      self.pi.write(self.gpio_power, 0)
    # Callback functions on table status change
    self.onVacant=onVacant
    self.onOccupied=onOccupied
    # Configuration variables
    self.activity_num_to_occupied = 3
    self.activity_time_debounce   = .5 
    self.activity_time_unoccupied = 20
    self.activity_time_reset      = 4
    self.activity_time_reoccupied = None
    # Pins which mirrors sensor output and table status
    self.outputSensor=False
    self.outputStatus=False
    # Variables to set heartbeat of this thread and recieve heartbeat of main thread
    self.hearttime    = time.time()
    self.heartmain    = 0
    # Status variables
    self.allwaysOn    = 0
    self.allwaysOff   = 0
    self.singleOn     = 0
    self.table_occupied = False
    self.move_time    = 0
    self.move_num     = 0
    self.lastactivity = 0
    self.lastchange   = time.time()
    self.buttontime   = 0

  # This function is called once to start the monitoring of the vibration sensor
  # Just runs an infinite loop, where it either waits for activity og vacancy
  # Runs external callback function when table status changes
  def run(self):
    self.tid=ctypes.CDLL('libc.so.6').syscall(224)
    log.info("Starting activity sensoring program (tid: %d)" % self.tid)
    # If sensor power is a gpio, then turn on sensor
    if self.gpio_power:
      log.debug("Turning on power to sensor")
      self.pi.write(self.gpio_power,1)
    # Main loop of activity thread
    while True:
      if self.table_occupied:
        log.debug("Waiting for vacant")
        self.wait_for_vacant()
        # Did we recieve a stop signal while we were wating?
        if self.stopsignal: break;
        # OK: Table is now vacant. Call onVacant callback, if it exists
        if self.onVacant: self.onVacant()
      else:
        log.debug("Waiting for occupied")
        self.wait_for_occupied()
        # Did we recieve a stop signal while we were wating?
        if self.stopsignal: break;
        # OK: Table is now occupied. Call onOccupied callback, if it exists
        if self.onOccupied: self.onOccupied()
    # We only get down here when activity thread is asked to quit
    # If power is configured. Turn off when exiting
    if self.gpio_power:
      log.debug("Turning off power to sensor")
      self.pi.write(self.gpio_power,0)
      self.pi.set_mode(self.gpio_power, pigpio.INPUT)

  def setAllwaysOn(self, state=False):
    log.info("Setting allwaysOn: %r" % state)
    self.allwaysOn=state
    self.allwaysOff=False

  def setAllwaysOff(self, state=False):
    log.info("Setting allwaysOff: %r" % state)
    self.allwaysOff=state
    self.allwaysOn=False

  def turnOn(self):
    self.singleOn = True

  def start(self):
    self.thread=threading.Thread(target=self.run, name="Activity")
    self.thread.start()
    self.stopsignal=False

  def stop(self):
    self.stopsignal=True

  def click(self):
    self.buttontime=time.time()

  def heartbeat(self):
    self.hearttime=time.time()
    # If we haven't heard from main thread in 2 minutes. Exit.
    if self.hearttime-self.heartmain > 120:
      log.debug("Main thread heartbeat too faint. Stoppong activity thread")
      self.stop()

  # Table is vacant
  # Wait for enough vibration triggers. Log each full hour with no activity
  # When ever a vibration is measured, check to see how long time passed
  #   since last vibration.
  def wait_for_occupied(self):
    waitbeat=0
    while True:
      self.heartbeat()
      if self.stopsignal: 
        log.debug("Stop signal - Breaking out of occupied wait")
        break
      if self.allwaysOff:
        time.sleep(3)
        continue
      # Wait for activity for a few seconds
      # Needs to be short (during devel), so we can break out fast on program exit
      if self.singleOn or self.allwaysOn or self.pi.wait_for_edge(self.gpio, pigpio.RISING_EDGE, 3):
        self.output("sensor",1)
        log.debug("Activity detected...")
        newtime=time.time()
        self.lastactivity=newtime
        waitbeat=0
        # Too long since last move - reset movements
        if newtime-self.move_time > self.activity_time_reset:
          log.debug("   long time since motion. Move_num reset...")
          self.move_num=0
        # This was an extra movement, so increase movement count
        self.move_num+=1
        log.debug("   Move_num new set to %d" % self.move_num)
        # Record time of latest movement
        self.move_time=newtime
        # If that was move_num movements in a row without "large" breaks,
        # ... then set table occupied and return from this function
        if self.move_num >= self.activity_num_to_occupied or self.singleOn or self.allwaysOn:
          if self.singleOn:
            log.info("Table turned on manually")
            self.singleOn=False
          if self.allwaysOn:
            log.info("Table turned on permanently")
          log.info("Table occupied - (vacant for %d seconds)" % (newtime-self.lastchange))
          self.lastchange=newtime
          self.table_occupied=True
          # Set output pin to high to indicate table occupied
          self.output("status",1)
          return(True)
        # We need more movements before we think the table is occupied.
        # But first sleep a little, tó ignore fast vibrations within a short time
        else:
          time.sleep(self.activity_time_debounce)
      # No vibration detected for 3600 seconds. Let the log file know
      else:
        waitbeat+=1
        if waitbeat%10==0:
          if waitbeat==10:       log.info("No activity for 30 seconds")
          elif waitbeat==100:    log.info("No activity for 5 minutes")
          elif waitbeat%1200==0: log.info("No activity last hour")


  def wait_for_vacant(self):
    while True:
      self.heartbeat()
      if self.stopsignal:
        log.debug("Stop signal - Breaking out of occupied wait")
        break
      if self.allwaysOn:
        time.sleep(3)
        continue
      # Wait a few seconds for activity
      if self.allwaysOff==0 and self.pi.wait_for_edge(self.gpio, pigpio.RISING_EDGE, 3):
        log.debug("Activity detected... Still occupied")
        self.lastactivity=time.time()
        self.buttontime=0
        self.output("sensor",1)
        self.move_num+=1 # Add 1 movement counter - people are still playing
        # Sleep a little, to ignore fast vibrations within a short time - no need to run this loop 1000 times/s
        time.sleep(3)
      else:
        # 3 seconds passed with no activity. Check if enough time has passed, if not listen again
        # Check time since last activity or last button. If larger than limit, go to vacant
        newtime=time.time()
        if min(newtime-self.buttontime, newtime-self.lastactivity)<self.activity_time_unoccupied:
          continue
        # OK: Long activity break. Change table status to unoccupied
        self.output("status",0)
        log.info("Table vacant - (occupied for %d seconds, %d movements detected)" % 
          (newtime-self.lastchange, self.move_num))
        self.lastchange=newtime
        self.table_occupied=False
        return(True)

  # Define or undefine output GPIOs which mirrors the sensor reading and/or table status
  # May be used for instance for LED indicators
  def setOutput(self, sensorGPIO, statusGPIO):
    if sensorGPIO:
      self.outputSensor=sensorGPIO
      self.pi.set_mode(self.outputSensor, pigpio.OUTPUT)
      self.pi.write(self.outputSensor, 0)
    # Don't mirror sensor. If one is defined, remove it.
    elif self.outputSensor:
      self.pi.set_mode(self.outputSensor, pigpio.INPUT)
      self.outputSensor=False
      self.sensorcb = None
    if statusGPIO:
      self.outputStatus=statusGPIO
      self.pi.set_mode(self.outputStatus, pigpio.OUTPUT)
      self.pi.write(self.outputStatus, self.table_occupied)
    # Don't mirror status. If one is defined, remove it.
    elif self.outputStatus:
      self.pi.set_mode(self.outputStatus, pigpio.INPUT)
      self.outputStatus=False

  def output(self, sensor, level):
    if sensor=="sensor" and self.outputSensor:
      log.debug("Sensor output set to %d " % level)
      self.pi.write(self.outputSensor,level)
      threading.Timer(1.0, self.outputOff).start()
    elif sensor=="status" and self.outputStatus:
      log.debug("Status output set to %d " % level)
      self.pi.write(self.outputStatus,level)

  # Trigger function for vibration-sensor going low again.
  # Only used if sensor outputs are mirrored to another GPIO
  def outputOff(self):
    if self.outputSensor:
      log.debug("Sensor turned off")
      self.pi.write(self.outputSensor,0)

  def sensorOn():
    if self.gpio_power:
      self.pi.write(self.gpio_power,1)

  def sensorOff():
    if self.gpio_power:
      self.pi.write(self.gpio_power,0)
