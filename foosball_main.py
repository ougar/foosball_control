#!/usr/bin/python
# coding: utf-8

# Standard libraries
import time
import threading
import logging
import signal
import sys
import select

sys.path.append("/home/kristian/pythonlib")
# My own standard libraries
import pigpio
import kdate
import button

# Foosball libraries
import teamscore
import goaldetect
import activity
import external

# Should commands be read from stdin
interactive=False

if len(sys.argv)>1 and sys.argv[1]=="-i":
  interactive=True

# Setup activity logging options
filename="./log/activity.log"
log = logging.getLogger("Foosball")
# If interactive just use stdout otherwise send to logfile
if interactive: fh = logging.StreamHandler()
else:           fh = logging.FileHandler(filename)
fh.setFormatter(logging.Formatter('%(asctime)s %(module)s %(threadName)s - %(message)s'))
log.addHandler(fh)
log.setLevel(logging.DEBUG)

log.debug("Starting foosball main program")
if interactive: log.debug("Starting in interactive mode")
else:           log.debug("Starting in non-interactive mode")

# Signal names
signalnames = {signal.SIGINT:  "SIGINT",
               signal.SIGTERM: "SIGTERM",
               signal.SIGHUP:  "SIGHUP",
               signal.SIGUSR1: "SIGUSR1",
               signal.SIGUSR2: "SIGUSR2",
               }

# Bunch class to use in stead of dicts, for prettier "bundling"
class Bunch:
  def __init__(self, **kwds):
    self.__dict__.update(kwds)

class Foosball:

  def __init__(self):
    self.pi=pigpio.pi()
    self.active=False
    # Heartbeat of main thread
    self.hearttime=0
    self.starttime=time.time()
    # Create Activity object which watches table status with vibration sensor
    self.activity=activity.Activity(self.pi, gpio=17, onVacant=self.vacant, onOccupied=self.occupied)
    # Create Goaldetect object which watches for goals using the laser sensors
    self.goaldetect=goaldetect.GoalDetect(self.pi, power=9, detect1=10, detect2=11, onGoal=self.goal)
    # Create dictionary to hold team info: scoreboards, buttons and current score
    self.team={1: Bunch(), 2: Bunch()}
    # Create Team 1 scoreboard + 2 buttons
    self.team[1].scoreboard = teamscore.TeamScore(self.pi, clock=22, data=27, load=23)
    self.team[1].up         = button.Button(pi=self.pi, gpio=25, callback=self.scoreCorrect, args=[1,1])
    self.team[1].down       = button.Button(pi=self.pi, gpio=18, callback=self.scoreCorrect, args=[1,-1])
    self.team[1].score      = 0
    self.team[2].scoreboard = teamscore.TeamScore(self.pi, clock=22, data=27, load=24)
    self.team[2].up         = button.Button(pi=self.pi, gpio=7, callback=self.scoreCorrect, args=[2,1])
    self.team[2].down       = button.Button(pi=self.pi, gpio=8, callback=self.scoreCorrect, args=[2,-1])
    self.team[2].score      = 0
    # Make sure scoreboards use the same lock, since they share clock and data gpio pins
    self.team[2].scoreboard.setLock(self.team[1].scoreboard.getLock())
    # Create Menu object
    # TO DO
    # Create external fileupdater object
    self.external=external.External(cbSetScore=self.setFromExternal)
    # Listen and catch signals to end program
    self.signalbreak=0
    signal.signal(signal.SIGTERM, self.sigterm)
    signal.signal(signal.SIGINT,  self.sigterm)

  def sigterm(self, signo, frame):
    log.info("Signal %s recieved. Setting signalbreak to exit main loop" % signalnames[signo])
    self.signalbreak=1

  # Called when a goal is detected in goaldetect
  def goal(self,team):
    self.activity.click()
    self.team[team].score+=1
    self.team[team].scoreboard.goal()
    self.setExternal()
    # Something check for win-condition???

  # Called when a goalcorrection button is pressed/released in a teamscore object
  # Buttondown is True on button-press and False on button release
  # Team is 1 or 2 deoending on which teams scoreboard is pressed
  # Updown is -1 for goaldown button and +1 for goalup button
  def scoreCorrect(self, gpio, buttondown, tick, team, updown):
    #print "ScoreCorrect: gpio=%d, buttondown=%d, team=%d, updown=%d" % (gpio, buttondown, team, updown)

    # Special case: If all 4 scorecorrect buttons are pressed, take that as a special case.
    # Toggle allways off
    # Players can use that to disable scoreboards, if they donøt like them.
    # WIP: Needs buttons to NOT be completely disabled onVacant, since that means,
    #      that you cant turn te scoreboards back on
    if (self.team[1].up.pressed and self.team[1].down.pressed and
        self.team[2].up.pressed and self.team[2].down.pressed):
      newstate=not self.activity.allwaysOff
      self.activity.setAllwaysOff(newstate)
      if newstate==False:
        self.activity.turnOn()
        time.sleep(.3)

    # What to do if the table is vacant/inactive?
    if self.active==False:
      st="pressed" if buttondown==True else "released"
      updown="up" if updown==1 else "down"
      log.info("Team %d %s-button %s while inactive. Ignoring" % (team, updown, st))
      return True

    # Let activity sensor know, that a button was clicked
    self.activity.click()

    # On button release, set external result file
    # - But only if no buttons are still pressed, otherwise we do it twice after double-button-reset
    if buttondown==False:
      if self.team[team].up.pressed==0 and self.team[team].down.pressed==0:
        self.setExternal()
      return True


    # If scoredown clicked, and score is allready 0, then do nothing
    if (self.team[team].score==0 and updown==-1): return

    # If both team up and down buttons are pressed, reset score and cancel repeat
    if (self.team[team].up.pressed and self.team[team].down.pressed):
      log.debug("Button score reset for team %d" % team)
      self.team[team].up.repeatClear()
      self.team[team].down.repeatClear()
      score=0
    # Else correct current score with updown and update scoreboard and external score
    else:
      score=self.team[team].score+updown
    # Call scorebord correct function to update led-display and update external score file
    self.setTeamScore(team, score)
    return True

  # Dont let scores go below 0 and start over at 0 if we get above 100
  def nfix(self,score):
    return(max(score,0)%100)

  def setTeamScore(self, team, score):
    self.team[team].score=self.nfix(score)
    self.team[team].scoreboard.scoreCorrect(self.team[team].score)

  def setExternal(self):
    self.external.setScore(self.team[1].score, self.team[2].score)

  def setFromExternal(self, score1, score2):
    if self.active==False:
      log.debug("Turning table on and waiting for comfirmation")
      self.activity.turnOn()
      while not self.active:
        time.sleep(.3)
    self.setTeamScore(1, score1)
    self.setTeamScore(2, score2)
    self.setExternal()
    self.team[1].scoreboard.blinkStart()
    self.team[2].scoreboard.blinkStart()

  # Called to set the score - for instance by external object on signal
  # or by a resetScore from the menu
  def setScore(self, score1, score2):
    if score1==0 and score2==0:
      self.resetScore()
    else:
      self.setTeamScore(1, score1)
      self.setTeamScore(2, score2)
      self.setExternal()

  # Called if setScore is setting the score to 0-0
  def resetScore(self):
    log.info("Resetting table score")
    self.team[1].score=0
    self.team[2].score=0
    self.team[1].scoreboard.reset() # Use reset to allow for possible blinks
    self.team[2].scoreboard.reset() # Use reset to allow for possible blinks
    self.setExternal()

  def heartbeat(self):
    self.hearttime=time.time()
    self.activity.heartmain=self.hearttime
    if self.hearttime-self.activity.hearttime > 60:
      log.debug("No heartbeat from external thread for 1 minute. Stopping program")
      self.stop()

  def start(self):
    log.info("Starting Foosball control class instance")
    self.heartbeat()
    self.external.start()
    self.activity.start()

  def stop(self):
    # Turn off all equipment on all pins
    log.debug("Stopping activity sensor thread")
    if self.goaldetect.active: self.goaldetect.stop()
    log.debug("Calling scoreboard shutdown")
    if self.team[1].scoreboard.active: self.team[1].scoreboard.shutdown()
    if self.team[2].scoreboard.active: self.team[2].scoreboard.shutdown()
    log.debug("Deassigning goal correction buttons")
    self.team[1].up.deactivate()
    self.team[1].down.deactivate()
    self.team[2].up.deactivate()
    self.team[2].down.deactivate()
    # Stop activity sensor and wait for the thread to return (max ca. 10 seconds)
    self.activity.stop()
    self.activity.thread.join()
    log.debug("Activity thread joined")
    log.debug("Stopping pi instance")
    self.pi.stop()
    self.external.deletePidFile()

  def vacant(self):
    self.active=False
    self.external.setVacant(1)
    self.team[1].scoreboard.shutdown()
    self.team[2].scoreboard.shutdown()
    self.goaldetect.stop()
    log.info("Bordet er ledigt")

  def occupied(self):
    self.external.setVacant(0)
    self.resetScore()
    self.active=True
    self.team[1].scoreboard.wakeup()
    self.team[2].scoreboard.wakeup()
    self.goaldetect.start()
    log.info("Bordet er nu optaget")

# Create a new Foosball instance and start it
foosball=Foosball()
foosball.start()
time.sleep(3)

# Main loop. Only actions are:
#  1: Log status
#  2: Report a heartbeat to the "watchdog"
#  3: Refresh score displays periodically, to recover from random mistakes
try:
  log.debug("Entering main loop")
  n=60
  mainbeat=0;
  while True:
    foosball.heartbeat()
    foosball.external.setHeartbeat()
    try:
      command=""
      # Should we take commands from stdin, then wait 60 seconds for command
      if interactive:
        i, o, e = select.select( [sys.stdin], [], [], 60 )
        if i:
          command=sys.stdin.readline().strip()
      # Else just sleep for 60 seconds
      else:
        time.sleep(60)

      if   command=="":  pass
      elif command=="q": foosball.signalbreak=1
      elif command=="i": foosball.activity.setAllwaysOff(not foosball.activity.allwaysOff)
      elif command=="a": foosball.activity.setAllwaysOn(not foosball.activity.allwaysOn)
      elif command=="r": foosball.resetScore()
      elif command.isdigit(): foosball.setScore(int(command),foosball.team[2].score)
      else:
        log.info("Unknown command %s recieved" % command)
    # If exception was caught from select due to signal, then ignore
    except select.error:
      pass

    if threading.activeCount()<3:
      log.debug("Number of threads is lower than 3. Seems strange. Quitting")
      break
      
    if foosball.signalbreak: 
      log.debug("Shutdown order given - Exiting main loop")
      break
    mainbeat+=1
    if mainbeat%100==0:
      q=time.time()
      log.info("Main loop %d loops." % mainbeat)

# If we stop - for any reason - stop foosball instance.
finally:
  log.debug("Running finally cleanup code")
  foosball.stop()
