#!/usr/bin/python
# coding: utf8

import pigpio
import teamscore

pi=pigpio.pi()
score1=teamscore.TeamScore(pi, clock=22, data=27, load=23)
score1=teamscore.TeamScore(pi, clock=22, data=27, load=24)
