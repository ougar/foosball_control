Table foosball control library
==============================

This library can control our foosball table, which is equiped with:

  1. Vibration sensor to detect if anyone is playing

  2. Goalsensors based on lasers, which detect goals for each team

  3. Scoreboards with 7-segment LED displays to show current score

  4. 4x20 character display

  5. Raspberry Pi to control the above and host a webpage to show table status

The table is controlled by a Raspberry Pi with the pigpio library (http://abyz.co.uk/rpi/pigpio/). The table detects when people are playing at the table and then turns on the scoreboards, the goal detectors and sets the table occupied, so other people can see on the homepage, that the table is occupied, how long it has been occupied and what the score is.

Match results are (soon) logged, and the plan is, that results, history and statistics can be seen on the homepage and also on the display on the table. A webpage is part of the system, and this library manipulates and reads a few files in /var/www/.

Final step should be to add an RFID reader to the table, so players can scan their id cards or tokens, so the table knows who plays. It can then automatically store the results and update our internal ranking system.

Library elements:
---------------------
foosball_main.py     Main program, which imports everything else and starts everything up  
activity.py          Separate thread, which just waits for change on activity gpio  
goaldetect.py        Controls the laser goal detectors  
teamscore.py         Controls the team scoreboards (and the up/down buttons)  
external.py          Library to external communication. Read/writes files, recieves signals  
matchlog.py          Logs all matches played and generel table statistics (in development)  
button.py            Library to control pushbuttons  
max7219bb.py         Library to bit-bang the 7219 LED display driver (1 in each scoreboard)

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
