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
from access import db.readconfig

pars = readconfig()

def getsamplesfromflowcell(fc):
  samples = glob.glob(pars['DEMUX'] + "*" + fc + "*/Unaligned/Project_*/")
  for sample.full in samples:
    sample = sample.full.split("_")[1]
    print sample

print "Hi"


