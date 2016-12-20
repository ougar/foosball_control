Table foosball control library
==============================

This library can control our foosball table, which is equiped with:

  1: Vibration sensor to detect if anyone is playing

  2: Goalsensors bases on lasers, which detect goals for each team

  3: Scoreboards with 7-segment LED displays to show current score

  4: 4x20 character display

Everything is controlled through this library.

A webpage is also part of the system, and this library manipulates and reads a few files in /var/www/

Library elements:
---------------------
foosball_main.py     Main program, which imports everything else and starts everything up

activity.py          Separate thread, which just waits for change on activity gpio

goaldetect.py        Controls the laser goal detectors

teamscore.py         Controls the team scoreboards (and the up/down buttons)

external.py          Library to external communication. Read/writes files, recieves signals

matchlog.py          Logs all matches played and generel table statistics

Still not functioning menu system
---------------------------------
config.py            Table configuration library

system.conf          Current table configuration file

lcdui.py             Prints text to the 4x20 character display

menu.py              Menu-system for 4x20 character display

menu.xml             Menu definition file in xml format. Defines all menu items and actions

Test programs for all individual libraries
------------------------------------------
test_activity.py                Listen for activity events

test_goaldetect.py              Use key to turn on/off lasers and listen for goals

test_lcdmenu.py                 Test menu system

test_scoreboards_1.py           Turn on display 1 and use up/down buttons

test_scoreboards_2.py           Turn on display 2 and use up/down buttons

test_scoreboards_pattern.py     Experimentation with animation patterns

test_scoreboards_turnoff.py     Turns both displays off
