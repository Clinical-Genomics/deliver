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
  query = (" SELECT GROUP_CONCAT(DISTINCT sample.sample_id) AS id, GROUP_CONCAT(DISTINCT flowcellname) AS fc, " + 
           " GROUP_CONCAT(DISTINCT lane ORDER BY lane) AS lanes, ROUND(SUM(readcounts)/2000000,2) AS M_reads, " +
           " GROUP_CONCAT(ROUND(q30_bases_pct,2) ORDER BY lane) AS q30, GROUP_CONCAT(ROUND(mean_quality_score,2) ORDER BY lane) AS score " + 
           " FROM sample, unaligned, flowcell " + 
           " WHERE sample.sample_id = unaligned.sample_id AND unaligned.flowcell_id = flowcell.flowcell_id " +
           " AND samplename LIKE '" + sample + "%' GROUP BY flowcell.flowcell_id")
  with db.create_tunnel(pars['TUNNELCMD']):
    with db.dbconnect(pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], 
                   pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']) as dbc:
      replies = dbc.generalquery( query )
      print len(replies), sample
  return replies
    
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

smpls = getsamplesfromflowcell(params, fc)

for sample in smpls.iterkeys():
  print sample
  dbinfo = getsampleinfofromname(params, sample)
  rc = 0
  fclanes = {}
  cnt = 0
  for info in dbinfo:
    print str(info)
    if (info['q30'] > 80):
      cnt += 1
      rc += info['M_reads']
      fclanes[cnt] = info['fc'] + "_" + info['lanes']
  if (rc > 75):
    print "pass " + str(rc) + " M reads " + str(fclanes)
  else:
    print "fail " + str(rc) + " M reads " + str(fclanes)
    
