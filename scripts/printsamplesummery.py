#!/usr/bin/python
#

from __future__ import print_function
import sys
import glob
import re
import os
from access import db, lims

def getsamplesfromflowcell(demuxdir, flwc):
  samples = glob.glob("{demuxdir}*{flowcell}*/Unalign*/Project_*/Sample_*".\
    format(demuxdir=demuxdir, flowcell=flwc))
  fc_samples = {}
  for sample in samples:
    sample = sample.split("/")[-1].split("_")[1]
    sample = sample.rstrip('BF') # remove the reprep (B) and reception control fail (F) letters from the samplename
    fc_samples[sample] = ''
  return fc_samples

def getsampleinfofromname(pars, sample):
  query = (" SELECT sample.sample_id AS id, samplename, flowcellname AS fc, " + 
           " lane, ROUND(readcounts/2000000,2) AS M_reads, " +
           " ROUND(q30_bases_pct,2) AS q30, ROUND(mean_quality_score,2) AS score " + 
           " FROM sample, unaligned, flowcell " + 
           " WHERE sample.sample_id = unaligned.sample_id AND unaligned.flowcell_id = flowcell.flowcell_id " +
           " AND (samplename LIKE '{sample}_%' OR samplename = '{sample}')".format(sample=sample))
  with db.create_tunnel(pars['TUNNELCMD']):
    with db.dbconnect(pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], 
                   pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']) as dbc:
      replies = dbc.generalquery( query )
  return replies

def main(argv):

  outputdir = '/mnt/hds/proj/bioinfo/MIP_ANALYSIS/'
  
  fc = None
  if len(argv) > 0:
    try:
      argv[0]
    except NameError:
      sys.exit("Usage: {} <flowcell name>".format(__file__))
    else:
      fc = argv[0]
  else:
    sys.exit("Usage: {} <flowcell name>".format(__file__))

  params = db.readconfig("non")
  smpls = getsamplesfromflowcell(params['DEMUXDIR'], fc)

  for sample in smpls.iterkeys():
    family_id = None
    cust_name = None
    with lims.limsconnect(params['apiuser'], params['apipass'], params['baseuri']) as lmc:
      analysistype = lmc.getattribute('samples', sample, "Sequencing Analysis")
      if analysistype is None:
        print("WARNING: Sequencing Analysis tag not defined for {}".format(sample))
        # skip to the next sample
        continue
      readcounts = .75 * float(analysistype[-3:])    # Accepted readcount is 75% of ordered million reads
      family_id = lmc.getattribute('samples', sample, 'familyID')
      cust_name = lmc.getattribute('samples', sample, 'customer')
      if not re.match(r'cust\d{3}', cust_name):
        print("WARNING '{}' does not match an internal customer name".format(cust_name))
        cust_name = None
      if cust_name == None:
        print("WARNING '{}' internal customer name is not set".format(sample))
      if family_id == None:
        print("WARNING '{}' family_id is not set".format(sample))

    dbinfo = getsampleinfofromname(params, sample)
    rc = 0         # counter for total readcount of sample
    fclanes = []   # list to keep flowcell names and lanes for a sample
    for info in dbinfo:
      if (info['q30'] > 80):     # Use readcount from lane only if it satisfies QC [=80%]
        rc += info['M_reads']
        fclanes.append(dict(( (key, info[key]) for key in ['fc', 'q30', 'lane'] )))
    if readcounts:
      if (rc > readcounts):        # If enough reads are obtained do
        print("{sample} Passed {readcount} M reads\nUsing reads from {fclanes}".format(sample=sample, readcount=rc, fclanes=fclanes))
      else:                        # Otherwise just present the data
        print("{sample} FAIL with {readcount} M reads.\n"
              "Requested with {reqreadcount} M reads.\n"
              "These flowcells summarized {fclanes}".format(sample=sample, readcount=rc, fclanes=fclanes, reqreadcount=readcounts))
    else:
      print("{} - no analysis parameter specified in lims".format(sample))

if __name__ == '__main__':
  main(sys.argv[1:])
