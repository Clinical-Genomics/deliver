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

outputdir = '/mnt/hds/proj/bioinfo/tmp/MIPP/exomes/'

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

fc_samples = {}
def getsamplesfromflowcell(pars, flwc):
  samples = glob.glob(pars['DEMUXDIR'] + "*" + flwc + "*/Unalign*/Project_*/Sample_*")
  for sampl in samples:
    sample = sampl.split("/")[len(sampl.split("/"))-1].split("_")[1]
    fc_samples[sample] = ''
  return fc_samples

def getsampleinfofromname(pars, sample):
  query = (" SELECT sample.sample_id AS id, samplename, flowcellname AS fc, " + 
           " lane, ROUND(readcounts/2000000,2) AS M_reads, " +
           " ROUND(q30_bases_pct,2) AS q30, ROUND(mean_quality_score,2) AS score " + 
           " FROM sample, unaligned, flowcell " + 
           " WHERE sample.sample_id = unaligned.sample_id AND unaligned.flowcell_id = flowcell.flowcell_id " +
           " AND (samplename LIKE '" + sample + "_%' OR samplename = '" + sample + "')")
  with db.create_tunnel(pars['TUNNELCMD']):
    with db.dbconnect(pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], 
                   pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']) as dbc:
      replies = dbc.generalquery( query )
  return replies

def makelinks(samplename, lanedict):
  if os.path.exists(outputdir + samplename):
    print outputdir + samplename + ' exists, has data already been exported?'
    return
  else:
    os.makedirs(outputdir + samplename)
    for entry in lanedict:
      fclane = lanedict[entry].split("_")
      print fclane
      fastqfiles = glob.glob(params['DEMUXDIR'] + "*" + fclane[0] + "*/Unalign*/Project_*/Sample_*" + 
                            samplename + "_*/*L00" + fclane[2] + "*gz")
      for fastqfile in fastqfiles:
        nameparts = fastqfile.split("/")[len(fastqfile.split("/"))-1].split("_")
        date_fc = fastqfile.split("/")[6].split("_")[0] + "_" + fastqfile.split("/")[6][-9:]
        newname = (nameparts[3][-1:] + "_" + date_fc + "_" + samplename + "_" + nameparts[2] +
                   "_" + nameparts[4][-1:] + ".fastq.gz")
        print fastqfile
        print newname
        os.symlink(fastqfile, outputdir + samplename + "/" + newname)

smpls = getsamplesfromflowcell(params, fc)

for sample in smpls.iterkeys():
  with lims.limsconnect(params['apiuser'], params['apipass'], params['baseuri']) as lmc:
    analysistype = lmc.getattribute('samples', sample, "Sequencing Analysis")
    readcounts = .75 * float(analysistype[-3:])    # Accepted readcount is 75% of ordered million reads
  dbinfo = getsampleinfofromname(params, sample)
  rc = 0         # counter for total readcount of sample
  fclanes = {}   # dict to keep flowcell names and lanes for a sample
  cnt = 0        # counter used in the dict to keep folwcell/lane count
  for info in dbinfo:
    if (info['q30'] > 80):     # Use readcount from lane only if it satisfies QC [=80%]
      cnt += 1
      rc += info['M_reads']
      fclanes[cnt] = info['fc'] + "_" + str(info['q30']) + "_" + str(info['lane'])
  if readcounts:
    if (rc > readcounts):        # If enough reads are obtained do
      print sample + " Passed " + str(rc) + " M reads\nUsing reads from " + str(fclanes)
      makelinks(sample, fclanes)
    else:                        # Otherwise just present the data
      print sample + " Fail " + str(rc) + " M reads\nThese flowcells summarixed " + str(fclanes)
  else:
    print sample + " - no analysis parameter specified in lims"

