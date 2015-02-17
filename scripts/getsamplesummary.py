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
from access import db, lims

fc_samples = {}
def getsamplesfromflowcell(pars, flwc):
  samples = glob.glob(pars['DEMUXDIR'] + "*" + flwc + "*/Unaligned/Project_*/Sample_*")
  for sampl in samples:
    sample = sampl.split("/")[len(sampl.split("/"))-1].split("_")[1]
    fc_samples[sample] = ''
  return fc_samples
  
def getsampleinfofromname(pars, sample):
  query = """" SELECT sample_id, flowcellname, lane, readcounts, q30_bases_pct, mean_quality_score FROM sample, unaligned, flowcell 
              WHERE sample.sample_id = unaligned.sample_id AND unaligned.flowcell_id = flowcell-flowcell_id 
              AND samplename = '""" + sample + """' """
  with create_tunnel(pars['TUNNELCMD']):
    with dbconnect(pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], 
                   pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']) as dbc:
      replies = dbc.generalquery( query )
      print len(replies), sample
    
    
    
fc = "flowcell"

if len(sys.argv) > 0:
  try:
    sys.argv[1]
  except NameError:
    sys.exit("Usage: " + sys.argv[0] + " <flowcell name>")
  else:
    fc = sys.argv[1]
else:
  sys.exit("Usage: " + sys.argv[0] + " <flowcell name>")

params = db.readconfig("non")

smpls = getsamplesfromflowcell(fc)

for sample in smpls.iterkeys():
  print sample
  dbinfo = getsampleinfofromname(params, sample)

