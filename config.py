import ConfigParser, os

class Config:

  def __init__(self, filename):
    self.config=ConfigParser.ConfigParser()
    self.config.read("system.conf")

  def setParam(self, param, value):
    pass

  def showall(self):
    for c in self.config.sections():
      print "["+c+"]"
      for o in self.config.options(c):
        value=self.config.get(c,o)
        print "  "+o+" = "+value
      print ""
