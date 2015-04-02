#!/usr/bin/python
#

from __future__ import print_function
import sys
import datetime
import time
import glob
import re
import socket
import os
import os.path
import select
from access import db, lims

def getsamplesfromflowcell(pars, flwc):
  samples = glob.glob(pars['DEMUXDIR'] + "*" + flwc + "*/Unalign*/Project_*/Sample_*")
  fc_samples = {}
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

def makelinks(demuxdir, outputdir, family_id, cust_name, sample_name, lanes):
    try:
      os.makedirs(os.path.join(outputdir, 'exomes', sample_name, 'fastq'))
    except OSError:
      pass
    for entry in lanes:
      fclane = lanes[entry].split("_")
      print(fclane)
      fastqfiles = glob.glob(demuxdir + "*" + fclane[0] + "*/Unalign*/Project_*/Sample_*" + 
                            sample_name + "[BF]_*/*L00" + fclane[2] + "*gz")
      for fastqfile in fastqfiles:
        nameparts = fastqfile.split("/")[len(fastqfile.split("/"))-1].split("_")
        date_fc = fastqfile.split("/")[6].split("_")[0] + "_" + fastqfile.split("/")[6][-9:]
        newname = (nameparts[3][-1:] + "_" + date_fc + "_" + sample_name + "_" + nameparts[2] +
                   "_" + nameparts[4][-1:] + ".fastq.gz")
        print(fastqfile)
        print(os.path.join(outputdir, 'exomes', sample_name, 'fastq', newname))
        try:
          os.symlink(fastqfile, os.path.join(outputdir, 'exomes', sample_name, 'fastq', newname))
        except:
          print("Can't create symlink for {}".format(sample_name))
        try:
          if cust_name != None and family_id != None:
            mip_outdir = os.path.join(outputdir, cust_name, family_id, 'exomes')
            link_source = os.path.join(outputdir, 'exomes', sample_name)
            print('mkdir {}'.format(mip_outdir))

            os.makedirs(mip_outdir)
            os.symlink(link_source, os.path.join(mip_outdir, sample_name))
        except:
          print("Can't create symlink for {} in MIP_ANALYSIS/cust".format(sample_name))

def main(argv):

  outputdir = '/mnt/hds/proj/bioinfo/MIP_ANALYSIS/'
  
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
    family_id = None
    cust_name = None
    with lims.limsconnect(params['apiuser'], params['apipass'], params['baseuri']) as lmc:
      pure_sample = sample.rstrip('BF') # remove the reprep (B) and reception control fail (F) letters from the samplename
      analysistype = lmc.getattribute('samples', pure_sample, "Sequencing Analysis")
      readcounts = .75 * float(analysistype[-3:])    # Accepted readcount is 75% of ordered million reads
      family_id = lmc.getattribute('samples', pure_sample, 'familyID')
      cust_name = lmc.getattribute('samples', pure_sample, 'customer')
      if not re.match(r'cust\d{3}', cust_name):
        print("'{}' does not match an internal customer name".format(cust_name))
        cust_name = None
    dbinfo = getsampleinfofromname(params, pure_sample)
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
        print(pure_sample + " Passed " + str(rc) + " M reads\nUsing reads from " + str(fclanes))
        makelinks(demuxdir=params['DEMUXDIR'], outputdir=outputdir, family_id=family_id, cust_name=cust_name, sample_name=pure_sample, lanes=fclanes)
      else:                        # Otherwise just present the data
        print(pure_sample + " Fail " + str(rc) + " M reads\nThese flowcells summarixed " + str(fclanes))
    else:
      print(pure_sample + " - no analysis parameter specified in lims")

if __name__ == '__main__':
  main(sys.argv[1:])
