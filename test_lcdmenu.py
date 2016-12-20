#!/usr/bin/python

import xml.etree.ElementTree as etree
import menu
import readchar
import config
import lcdui

e = etree.parse('menu.xml').getroot()

q=menu.Item(0,0)

menu = menu.Menu().fromxml(e)

config = config.Config("system.conf")

#config.showall()
#exit()

#menu.rprint()

device = lcdui.lcd(0x27,1,True,False)

while True:
  a=menu.display()
  for (idx,val) in enumerate(a):
    device.lcd_puts(val,idx+1)
  #device.lcd_puts("  Tilbage           ",2);
  #device.lcd_puts("* Statistik         ",3);
  #device.lcd_puts("  Netvaerk          ",4);
  print ""
  menu.rprint()
  a=readchar.readchar()
  if a=='o': q=-1
  elif a=='k': q=0
  elif a=='m': q=1
  elif a=='q': exit()
  else: continue
  if (menu.execute(q)==-10): exit()
