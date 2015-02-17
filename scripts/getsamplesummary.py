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

def getsamplesfromflowcell(flwc):
  print flwc
  samples = glob.glob(pars['DEMUXDIR'] + "*" + flwc + "*/Unaligned/Project_*/Sample_*")
  for sampl in samples:
    smpl = sampl.split("/")[len(sampl.split("/"))-1].split("_")[1]
    print smpl
  return samples

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

smpls = getsamplesfromflowcell(fc)


print "Hi"


