#!/usr/bin/python
#

from __future__ import print_function
import sys
import glob
import re
import os
import os.path
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '0.8.1'

def getsamplesfromflowcell(demuxdir, flwc):
  samples = glob.glob("{demuxdir}*{flowcell}/Unalign*/Project_*/Sample_*".\
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
             " FROM sample, unaligned, flowcell, demux " +
             " WHERE sample.sample_id = unaligned.sample_id AND unaligned.demux_id = demux.demux_id " +
             " AND demux.flowcell_id = flowcell.flowcell_id " +
             " AND (samplename LIKE '{sample}_%' OR samplename = '{sample}')".format(sample=sample))
    with db.create_tunnel(pars['TUNNELCMD']):
        with db.dbconnect(pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], 
                       pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']) as dbc:
            replies = dbc.generalquery( query )
    return replies

def make_link(demuxdir, outputdir, family_id, cust_name, sample_name, fclane):
    fastqfiles = glob.glob(
        "{demuxdir}*{fc}/Unalign*/Project_*/Sample_{sample_name}_*/*L00{lane}*gz".format(
          demuxdir=demuxdir, fc=fclane['fc'], sample_name=sample_name, lane=fclane['lane']
        ))
    fastqfiles.extend(glob.glob(
        "{demuxdir}*{fc}/Unalign*/Project_*/Sample_{sample_name}[BF]_*/*L00{lane}*gz".format(
          demuxdir=demuxdir, fc=fclane['fc'], sample_name=sample_name, lane=fclane['lane']
        )))
  
    for fastqfile in fastqfiles:
        nameparts = fastqfile.split("/")[-1].split("_")
        rundir = fastqfile.split("/")[6]
        date = rundir.split("_")[0]
        newname = "{lane}_{date}_{fc}_{sample_name}_{index}_{readdirection}.fastq.gz".format(
          lane=fclane['lane'],
          date=date,
          fc=fclane['fc'],
          sample_name=sample_name,
          index=nameparts[-4],
          readdirection=nameparts[-2][-1:]
        )
  
        # first remove the link - might be pointing to wrong file
        dest_fastqfile = os.path.join(outputdir, 'exomes', sample_name, 'fastq', newname)
        try:
            os.remove(dest_fastqfile)
        except OSError:
            pass

        # then create it
        try:
            os.symlink(fastqfile, dest_fastqfile)
        except:
            print("Can't create symlink for {} in {}".format(sample_name, os.path.join(os.path.join(outputdir, 'exomes', sample_name, 'fastq', newname))))

        if cust_name != None and family_id != None:
            cust_dest_fastqfile = os.path.join(os.path.join(outputdir, cust_name, family_id, 'exomes', sample_name, 'fastq', newname))
            try:
                os.remove(cust_dest_fastqfile)
            except OSError:
                pass
            try:
                os.symlink(fastqfile, cust_dest_fastqfile)
            except:
                print("Can't create symlink for {} in {}".format(sample_name, os.path.join(os.path.join(outputdir, cust_name, family_id, 'exomes', sample_name, 'fastq', newname))))

def main(argv):

  print('Version: {} {}'.format(__file__, __version__))

  outputdir = '/mnt/hds/proj/bioinfo/tmp/MIP_ANALYSIS/'
  
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
  lims = Lims(BASEURI, USERNAME, PASSWORD)
  samples = getsamplesfromflowcell(params['DEMUXDIR'], fc)

  for sample_id in samples.iterkeys():
    print('Sample: {}'.format(sample_id))
    family_id = None
    cust_name = None

    try:
      sample = Sample(lims, id=sample_id)
      sample.get(force=True)
    except:
      try:
        print("WARNING: Sample {} not found in LIMS! Trying as CG ID...".format(sample_id), end='')
        # maybe it's an old CG ID
        sample = lims.get_samples(udf={'Clinical Genomics ID': sample_id})[0]
        print("Got it: {}".format(sample.id))
      except:
        print("WARNING: Sample {} still not found in LIMS!".format(sample_id))
        continue

    try:
      analysistype = sample.udf["Sequencing Analysis"]
    except KeyError:
      analysistype = None

    print('Application tag: {}'.format(analysistype))
    if analysistype is None:
      print("WARNING: Sequencing Analysis tag not defined for {}".format(sample_id))
      # skip to the next sample
      continue
    if analysistype == 'RML': # skip Ready Made Libraries
      print("WARNING: Ready Made Library. Skipping link creation for {}".format(sample_id))
      continue
    readcounts = .75 * float(analysistype[-3:])    # Accepted readcount is 75% of ordered million reads

    try:
      family_id = sample.udf['familyID']
    except KeyError:
      family_id = None
    try:
      cust_name = sample.udf['customer']
      if cust_name is not None:
        cust_name = cust_name.lower()
    except KeyError:
      cust_name = None
    if cust_name == None:
      print("WARNING '{}' internal customer name is not set".format(sample_id))
    elif not re.match(r'cust\d{3}', cust_name):
      print("WARNING '{}' does not match an internal customer name".format(cust_name))
      cust_name = None
    if family_id == None:
      print("WARNING '{}' family_id is not set".format(sample_id))

    dbinfo = getsampleinfofromname(params, sample_id)
    rc = 0         # counter for total readcount of sample
    fclanes = []   # list to keep flowcell names and lanes for a sample
    for info in dbinfo:
      if (info['q30'] > 80):     # Use readcount from lane only if it satisfies QC [=80%]
        rc += info['M_reads']
        fclanes.append(dict(( (key, info[key]) for key in ['fc', 'q30', 'lane'] )))
    if readcounts:
      if (rc > readcounts):        # If enough reads are obtained do
        print("{sample_id} Passed {readcount} M reads\nUsing reads from {fclanes}".format(sample_id=sample_id, readcount=rc, fclanes=fclanes))

        # try to create old dir structure
        try:
          os.makedirs(os.path.join(outputdir, 'exomes', sample_id, 'fastq'))
        except OSError:
          pass

        # try to create new dir structure
        if cust_name != None and family_id != None:
          try:
            os.makedirs(os.path.join(outputdir, cust_name, family_id, 'exomes', sample_id, 'fastq'))
          except OSError:
            pass
          try:
            os.makedirs(os.path.join(outputdir, cust_name, family_id, 'exomes', family_id))
          except OSError:
            pass

        # create symlinks for each fastq file
        for fclane in fclanes:
          make_link(
            demuxdir=params['DEMUXDIR'],
            outputdir=outputdir,
            family_id=family_id,
            cust_name=cust_name,
            sample_name=sample_id,
            fclane=fclane
          )
      else:                        # Otherwise just present the data
        print("{sample_id} FAIL with {readcount} M reads.\n"
              "Requested with {reqreadcount} M reads.\n"
              "These flowcells summarized {fclanes}".format(sample_id=sample_id, readcount=rc, fclanes=fclanes, reqreadcount=readcounts))
    else:
      print("{} - no analysis parameter specified in lims".format(sample_id))

if __name__ == '__main__':
  main(sys.argv[1:])
