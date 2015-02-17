#!/usr/bin/python
#
import sys
import datetime
import time
import glob
import re
import socket
import os
import select
from access import db

fc = "flowcell"
print sys.argv[1]
if len(sys.argv) > 0:
  try:
    sys.argv[1]
  except NameError:
    sys.exit("Usage: " + sys.argv[0] + " <flowcell name>")
  else:
    fc = sys.argv[1]
else:
  sys.exit("Usage: " + sys.argv[0] + " <flowcell name>")

pars = db.readconfig("non")

def getsamplesfromflowcell(fc):
  samples = glob.glob(pars['DEMUX'] + "*" + fc + "*/Unaligned/Project_*/")
  for sample.full in samples:
    sample = sample.full.split("_")[1]
    print sample

print "Hi"


