#!/usr/bin/python
# coding: utf8

import time
import kdate
import logging
import threading
import os
import ctypes
import json
#import docopt
#import sys
#import subprocess

log = logging.getLogger("Foosball")

class MatchLog:

  def __init__(self):
    self.stopsignal=False
    self.running=False
    self.hearttime=0
    self.heartmain=0
    self.log=[]

  def start(self):
    self.thread=threading.Thread(target=self.run, name="MatchLog")
    self.thread.start()
    self.stopsignal=False
    self.running=True
    self.heartbeat()

  def stop(self):
    self.stopsignal=True

  def heartbeat(self):
    self.hearttime=time.time()
    # If we haven't heard from main thread in 2 minutes. Exit.
    if self.heartmain and self.hearttime-self.heartmain > 120:
      log.debug("Main thread heartbeat too faint. Stoppong MatchLog thread")
      self.stop()

  def run(self):
    self.tid=ctypes.CDLL('libc.so.6').syscall(224)
    log.info("Starting MatchLog program (tid: %d)" % self.tid)
    # If sensor power is a gpio, then turn on sensor
    if self.gpio_power:
      log.debug("Turning on power to sensor")
      self.pi.write(self.gpio_power,1)
    # Main loop of activity thread
    while True:
      pass
 
class Match:
  def __init__(self):
    self.starttime=time.time()
    self.goallist=[]
    self.finishtime=False
    self.stamp=False

  def finish(self):
    self.finishtime=time.time()

  def goal(self, team, time, black, yellow):
    b=locals()
    del(b["self"])
    self.goallist.append(b)

if __name__ == '__main__':
  match=Match()
  match.goal(1,2,3,4)
  print(json.dumps(match.__dict__))
