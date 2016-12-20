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

goal1=0;
goal2=0;

def goal(team):
  global goal1, goal2
  if team==1:
    print "Team 1 scores"
    goal1+=1;
  else:
    print "Team 2 scores"
    goal2+=1;

# Create Goaldetect object which watches for goals using the laser sensors
pi=pigpio.pi()
gd=goaldetect.GoalDetect(pi, power=9, detect1=10, detect2=11, onGoal=goal)

try: 
  print "Starting goaldetection... (press 'q' to quit or 'a' to toggle table status"
  while True:
    print "Reading..."
    key=repr(readchar.readkey())
    print "Hej "+key+ " slut"
    if key=="'q'":
      break
    elif key=="'a'":
      if gd.active: 
        print "Stopping goaldetection"
        gd.stop()
      else:
        print "Starting goaldetection"
        gd.start()

except KeyboardInterrupt:
  print "Keyboard interrupt"

finally:
  print "Running cleanup code"
  gd.stop()
  pi.stop()
