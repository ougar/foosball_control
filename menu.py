import xml.etree.ElementTree as etree
import os

class Menu:

  def __init__(self, depth=0, index=0):
    self.depth=depth
    self.index=index
    self.title=""
    self.type=None
    self.items=[]
    self.function=None
    # Which menu is active
    self.active=1
    self.level=0

  # Parse XML structure and define menu and all child menus/items
  def fromxml(self, xmlmenu):
    # Add xml attributes as class attributes
    for attr in ["title","type","function","restricted"]:
      if xmlmenu.attrib.has_key(attr):
        setattr(self,attr,xmlmenu.attrib[attr])

    # Add default child-menu-items to go back/exit menu
    if self.depth==0: self.items.append(self.exititem())
    else:             self.items.append(self.backitem())

    # Run through all child xml elements. If element is a "menu"
    # add a menu. If element is an "item", add an item.
    for (index, element) in enumerate(xmlmenu, start=1):
      if element.tag=="menu":
        child=Menu(self.depth+1,index).fromxml(element)
      elif element.tag=="item":
        child=Item(self.depth+1,index).fromxml(element)
      else: raise MenuXMLError("Unknown element tag: %s" % element.tag)
        # Let child inherit parents action function
      if child.function is None:
        child.function=self.function
      self.items.append(child)
    return(self)

  # Display menu.
  def display(self):
    # If this is not the current active menu, ask to display active child
    if self.level>self.depth:
      return(self.items[self.active].display())
    # If this IS the correct active menu, make array with header line and 3 menu
    # items (or 2 if there is only 2). Middle (2nd) is the current active on
    # and the menu also shows the one before that and the one after that
    else:
      lines=["Menu: %-14s" % self.title]
      lines.append("  %-18s" % self.items[(self.active-1)%len(self.items)].title)
      lines.append("* %-18s" % self.items[self.active].title)
      if (len(self.items)>2):
        lines.append("  %-18s" % self.items[(self.active+1)%len(self.items)].title)
      else: lines.append(" " * 20)
      # When we are testing, clear the screen and print the menu
      os.system("clear")
      for q in lines:
         print q
      return(lines);

  def trigger(gpio, level, tick):
    self.display()

  # Whenever a menu button is pressed, we execute this function in the menu-root element
  # We then continue to execute the active child item, until we reach the correct depth.
  # The execute function is then run at this depth.
  # When we return we update the current level, if menu depth was changed further down
  # the chain.
  def execute(self, button):
    # If current active menu is below this menu, exccute active child element
    if self.level>self.depth:
      print("%sExecute - Pass on (level=%d,depth=%d)" % (" " * self.depth, self.level, self.depth))
      updown=self.items[self.active].execute(button)
      # And update current depth level, to account for menu movements down the chain
      self.level += updown
      return(updown)
    # This menu is the current one: 
    # If up/down button was pressed, move active element and display menu
    elif button!=0:
      print("%sExecute - Button pressed: %d (level=%d,depth=%d)" % (" " * self.depth, button, self.level, self.depth))
      self.active=(self.active+button)%len(self.items)
      return(0)
    # Else enter is pressed, execute active child, could be back, submenu or item
    else:
      # Get active child, which was executed
      c=self.items[self.active]
      print("%sExecute - Enter pressed. Child class,type: %s,%s (level=%d,depth=%d)" % (" " * self.depth, c.__class__.__name__, c.type, self.level, self.depth))
      # Child is Exit from root menu
      if   (c.type=="exit"): return(-10)
      # Child is back button
      elif (c.type=="back"):
        self.active=1                    #   .. reset this menu to element 1
        self.level-=self.depth           #   .. subtract depth from current level (below current level, level is always 0)
        return(-1)                       #   .. return -1 to all parent executers to update their level
      # Child is a sub menu
      elif (c.__class__.__name__ == "Menu"):
        self.level+=1                    #   .. Increase menu depth level
        c.level+=c.depth                 #   .. Increase level of active child to its depth (because level was 0)
        return(1)                        #   .. Return 1 to all parent executers to update their level
      # Child is an item
      elif (c.__class__.__name__== "Item"):
        self.level+=1                    # ... Increase current menu level
        c.level+=c.depth                 #   .. Increase level of active child to its depth (because level was 0)
        c.execute(0)                     # ... Execute child item
        return(1)                        # ... Return 1 to add to parents menu level

  def backitem(self):
    b=Item(self.depth+1,0)
    b.title="Tilbage"
    b.type="back"
    return(b)

  def exititem(self):
    b=Item(1,0)
    b.title="Afslut menu"
    b.type="exit"
    return(b)

  def mprint(self, mark=False):
    if mark: i1=bcolors.WARNING
    elif self.level==self.depth: i1=bcolors.OKGREEN
    else: i1=""
    if mark or self.level==self.depth: i2=bcolors.ENDC
    else: i2=""
    print "%s%sMenu %i: %s (d=%d, l=%d, a=%d)%s" % (i1,"  " * self.depth, self.index, self.title,self.depth,self.level, self.active,i2)

  def rprint(self, mark=False):
    self.mprint(mark)
    for q in self.items:
      if self.level==self.depth and q.index==self.active:
        q.rprint(True)
      else:
        q.rprint()


class Item:
  
  def __init__(self, depth, index):
    self.title="None"
    self.depth=depth
    self.index=index
    self.type=None
    self.function=None
    self.text=""
    self.isScrollable=False
    self.hasrun=False
    self.level=0
  
  def fromxml(self, xmlitem):
    self.title=xmlitem.text.strip()
    if xmlitem.attrib.has_key("type"):
      self.itype=xmlitem.attrib["type"]
    if xmlitem.attrib.has_key("function"):
      self.function=xmlitem.attrib["function"]
#    self.arg=arg
#    self.values=values
#    self.confirm=confirm
    return(self)

  def execute(self, button):
    if self.hasrun:
      print "Button pressed to exit item"
      self.level=0
      return(-1)
    else:
      self.hasrun=True
      print "Item executed: %s" % self.title

  def display(self):
    print("Og vi er tilbage i iteam %s" % self.title)
    

  def rprint(self, mark=False):
    if mark: i1=bcolors.WARNING
    elif self.level==self.depth: i1=bcolors.OKGREEN
    else: i1=""
    if mark or self.level==self.depth: i2=bcolors.ENDC
    else: i2=""
    print "%s%sItem %i: %s (%d)%s" % (i1,"  " * self.depth, self.index, self.title, self.level,i2)

class MenuXMLError(Exception):
  pass

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
