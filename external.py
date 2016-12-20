#!/usr/bin/python
# coding: utf8

import time
import logging
import threading
import datetime
import signal
import os

log = logging.getLogger("Foosball")

class External:

  def __init__(self, cbSetScore):
    self.fileStatus="/var/www/scoreboard/vacant.txt"
    self.fileScore="/var/www/scoreboard/score.txt"
    self.fileCorrect="/var/www/scoreboard/correctscore.txt"
    self.goalScript="/var/www/scoreboard/newgoal.sh"
    self.fileHeartbeat="/var/www/scoreboard/heartbeat"
    self.pidfile="/var/www/scoreboard/foosball_main.pid"
    self.cbSetScore=cbSetScore

  def runSignal(self, signo, frame):
    log.debug("Signal recieved - reading new score from scorecorrect-file")
    try:
      s1=""
      s2=""
      with open(self.fileCorrect, 'r') as f:
        s1 = f.readline().strip()
        s2 = f.readline().strip()
      t1=int(s1)
      t2=int(s2)
      self.cbSetScore(t1,t2)
    except:
      log.debug("Cannot parse file: %s (line1: %s, line2: %s)" % (self.fileCorrect, s1, s2))

  def setScore(self, team1, team2):
    log.debug("Setting score to external file: %d - %d" % (team1, team2))
    filename=self.fileScore
    with open(filename, "w") as text_file:
      text_file.write("%d - %d\n" % (team1, team2))
    return

  def setVacant(self,vacant):
    log.debug("Setting external vacant file to %d" % vacant)
    filename=self.fileStatus
    with open(filename, "w") as text_file:
      text_file.write("%d\n" % vacant)
    return

  def start(self):
    # Write PID file, so signals can reach us easily
    self.writePidFile()
    # Setup function runSignal to run if SIGUSR1 signal is recieved
    self.signal=signal.signal(signal.SIGUSR1, self.runSignal)
    # Initialize to score=0-0 and set table vacant
    self.setScore(0,0)
    self.setVacant(1)

  def writePidFile(self):
    pid = str(os.getpid())
    log.debug("Writing PID ("+pid+") to pidfile")
    with open(self.pidfile, 'w') as pidfile:
      pidfile.write(pid+"\n")
    return

  def deletePidFile(self):
    log.debug("Deleting PID file")
    os.remove(self.pidfile)
    return

  def setHeartbeat(self):
    t=time.time()
    tstr=datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
    #log.debug("Setting heartbeat to %s (%d)" % (tstr, t))
    filename=self.fileHeartbeat
    with open(filename, "w") as text_file:
      text_file.write("%d\n" % t)
    return
    
