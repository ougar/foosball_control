#!/usr/bin/python
# coding: utf8

import time
import pigpio

class Button:
  
  def __init__(self, pi, gpio, callback, debounce=50, pushlevel=0, args=False):
    self.pi=pi                # Pigpio instance
    self.gpio=gpio            # Which pin is the button attached to
    self.validGPIO()          # Check that the gpio is valid
    self.callback=callback    # Callback function on button press
    self.debounce=debounce    # How many ms should the button be debounced - default 50ms
    self.pushlevel=pushlevel  # When the button is pushed, what level is the gpio set to - default 0 
    self.args=args            # Extra argument to callback function
    # Repeat properties
    self.repeatstatus=0
    self.repeatinit=1000
    self.repeattime=200
    # Optional features properties - no doubleclicks, no long clicks
    self.doubletime=0        # Doubleclick default off (time=0)
    self.longtime=0          # Long presses default off (time=0)
    self.output=0            # Pin to write button status to (negative if reverse level)
    # Status properties
    self.lastexecute=None    # Tick when button was last executed
    self.lastpress=None      # Tick when button was last pressed
    self.lastrelease=None    # Tick when button was last released
    self.level=1-pushlevel   # Current level of button (not pressed initially)
    if pushlevel: self.pull=pigpio.PUD_DOWN # Button pulls pin high, so use pull down resistor
    else:         self.pull=pigpio.PUD_UP   # Button pulls pin low, so use pull up resistor
    self.pressed=0           # Is button currently pressed down
    self.startup=time.time() # Ignore triggers within the first 500 ms
    self.activate()          # Set up gpio-ports and callbacks

  # Cancel listen for button press. Deassign callback. Dont change gpio mode. Input is "safe"
  def deactivate(self):
    self.pi.set_glitch_filter(self.gpio,0)
    if self.cb: self.cb.cancel()
    else: raise ButtonException("No callback active. Can't deactivate")

  # Activate button, which means setting the GPIO to input and assigning callback function
  def activate(self, callback=False, gpio=False):
    if callback: self.callback=callback
    if gpio and self.validGPIO: self.gpio=gpio
    self.pi.set_mode(self.gpio, pigpio.INPUT)
    self.pi.set_pull_up_down(self.gpio, self.pull)
    # Sleep to let input pin settle before assigning callback
    time.sleep(.03)
    self.cb = self.pi.callback(self.gpio, pigpio.EITHER_EDGE, self.catcher)
    self.pi.set_glitch_filter(self.gpio, 1000*self.debounce)
    return(True)

  # Check if gpio-number is valid for this raspberry pi model
  # Type 1: Revision 2 and 3.         User gpios 0-1, 4, 7-11, 14-15, 17-18, 21-25
  # Type 2: Revision 4, 5, 6, and 15. User gpios 2-4, 7-11, 14-15, 17-18, 22-25, 27-31. <- My 2 old pies
  # Type 3: Revision 16+.             User gpios 2-27 (0 and 1 are reserved).
  def validGPIO(self,pinnumber=False):
    if not pinnumber: pinnumber=self.gpio
    if self.pi.get_hardware_revision()<=3:
      if pinnumber in [0,1,4]+range(7,12)+[14,15,17,18]+range(21,26): return True
    elif self.pi.get_hardware_revision()<=15:
      if pinnumber in [2,3,4]+range(7,12)+[14,15,17,18]+range(22,26)+range(27,32): return True
    else:
      if pinnumber in range(2,28): return True
    raise ButtonGPIOException("Invalid button GPIO")

  # Mirror the debounced button input on an output pin. Call with outgpio=False (or 0) to disable
  def enableOutput(self, outgpio, reverse=False):
    if outgpio==self.gpio: raise ButtonGPIOException("Output pin can't be the same is button input pin")
    if not self.validGPIO(outgpio): raise ButtonGPIOException("Invalid output GPIO number")
    # If output should be inverse of input pin, set pinumber to negative
    if reverse: outgpio=-outgpio
    # Output allready defined. Deactivate that output (set to input)
    if self.output:
      self.pi.set_mode(abs(self.output), pigpio.INPUT)
      self.output=0
    # New output gpio pin given. Set to OUTPUT and set level to 0. Correct level is set in self.catcher()
    if outgpio:
      self.output=outgpio
      self.pi.set_mode(abs(self.output), pigpio.OUTPUT)
      self.pi.write(abs(self.output), 0)

  # Activate or deactivate doubleclicks (if time<=0 then deactivate)
  # Doubleime is maximum time in seconds between clicks to count as doubleclicks
  def doubleclick(self, doubletime=.3):
    self.doubletime=doubletime

  # Activate ot deactivate longclicks (if time<=0 then deactivate)
  # Longtime is minimum time in seconds the button is pressed to count as a long click
  def longclick(self, longtime=1.5):
    self.longtime=longtime

  # Basic callback function. This function is triggered on all edge changes on button input pin
  # This function is NOT the callback function defined for the button by the user, which is  
  # called by the execute function.
  def catcher(self, gpio, level, tick):
    # Ignore triggers within the first 2 seconds of program start
    if self.startup:
      if time.time()-self.startup < 2: 
        self.startup=False
        return
    # If an output gpio is configured, set output to level
    if   self.output<0: pi.write(-self.output,1-level)
    elif self.output>0: pi.write(self.output, level)

    # Button is released. Record state and time
    if level==1-self.pushlevel: 
      self.lastrelease=tick 
      self.pressed=False
      self.repeatClear()
      # Call external callback with buttonlevel=False for key release event
      self.execute(gpio, False, tick)
      return True

    # Button was pressed. Do a whole lot of stuff
    elif level==self.pushlevel:
      self.lastpress=tick
      self.cancelrepeat=0
      self.pressed=True
      # Key was pressed, so record when key was last released. When that change, stop repeating
      initrelease=self.lastrelease
      # Run basic execution with buttonlevel True for key-press event
      self.execute(gpio, True, tick)
      self.pi.set_watchdog(self.gpio, self.repeatinit)
      self.repeatstatus=1
    # Level is 2 (not 0 or 1) so it is a watchdog timeout. Call execute again with keypress event
    else:
      # First repeat is longer, so first time we get here, set status=2 and make shorter watchdog
      if self.repeatstatus==1:
        self.repeatstatus=2
        self.pi.set_watchdog(self.gpio, self.repeattime)
      # Run execute-function thus repeating button click
      self.execute(gpio, True, tick)
    return True

  def repeatClear(self):
    self.pi.set_watchdog(self.gpio,0)
    self.repeatstatus=0

  # Manually trigger the button
  def trigger(self, level):
    self.execute(self.pi.get_current_tick(), level)
    return(True)

  # This function executes the external callback function defined by the user
  # The external function is called with variable number of arguments:
  #   1st argument: Current tick-value
  #   2nd argument: If self.args is defined, it is supplied as arg2
  #   3nd (or 2nd) argument: If clicktype is not 1 (single click), then
  #       clicktype is added as argument. Number means n-double clicks
  #       "long" means a long click.
  def execute(self, gpio, level, tick, clicktype=1):
    args=[gpio, level, tick]
    # Add extra arguments, if they are defined - args MUST be a list
    if self.args: args.extend(self.args)
    # Add clicktype argument, if it is not a single click
    if not clicktype==1: args.append(clicktype)
    # Call external callback function with argument list
    self.callback(*args)

class ButtonException(Exception): pass
class ButtonGPIOException(ButtonException): pass

