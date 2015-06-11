#!/usr/bin/python
#

from __future__ import print_function
import sys
import glob
import re
import os
from access import db, lims

__version__ = '0.3.0'

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

def make_link(demuxdir, outputdir, family_id, cust_name, sample_name, fclane):
    fastqfiles = glob.glob(
        "{demuxdir}*{fc}*/Unalign*/Project_*/Sample_{sample_name}_*/*L00{lane}*gz".format(
          demuxdir=demuxdir, fc=fclane['fc'], sample_name=sample_name, lane=fclane['lane']
        ))
    fastqfiles.extend(glob.glob(
        "{demuxdir}*{fc}*/Unalign*/Project_*/Sample_{sample_name}[BF]_*/*L00{lane}*gz".format(
          demuxdir=demuxdir, fc=fclane['fc'], sample_name=sample_name, lane=fclane['lane']
        )))
  
    for fastqfile in fastqfiles:
        nameparts = fastqfile.split("/")[-1].split("_")
        rundir = fastqfile.split("/")[6]
        date = rundir.split("_")[0]
        fc = rundir[-9:]
        newname = "{lane}_{date}_{fc}_{sample_name}_{index}_{readdirection}.fastq.gz".format(
          lane=nameparts[3][-1:],
          date=date,
          fc=fc,
          sample_name=sample_name,
          index=nameparts[2],
          readdirection=nameparts[4][-1:]
        )
  
        try:
            os.symlink(fastqfile, os.path.join(outputdir, 'exomes', sample_name, 'fastq', newname))
        except:
            print("Can't create symlink for {}".format(sample_name))
  
        if cust_name != None and family_id != None:
            try:
                os.symlink(fastqfile, os.path.join(os.path.join(outputdir, cust_name, family_id, 'exomes', sample_name, 'fastq', newname)))
            except:
                print("Can't create symlink for {} in {}".format(sample_name, os.path.join(os.path.join(outputdir, cust_name, family_id, 'exomes', sample_name, 'fastq', newname))))

def main(argv):

  print('Version: {} {}'.format(__file__, __version__))

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
    print('Sample: {}'.format(sample))
    family_id = None
    cust_name = None
    with lims.limsconnect(params['apiuser'], params['apipass'], params['baseuri']) as lmc:
      analysistype = lmc.getattribute('samples', sample, "Sequencing Analysis")
      print('Application tag: {}'.format(analysistype))
      if analysistype is None:
        print("WARNING: Sequencing Analysis tag not defined for {}".format(sample))
        # skip to the next sample
        continue
      if analysistype == 'RML': # skip Ready Made Libraries
        print("WARNING: Ready Made Library. Skipping link creation for {}".format(sample))
        continue
      readcounts = .75 * float(analysistype[-3:])    # Accepted readcount is 75% of ordered million reads
      family_id = lmc.getattribute('samples', sample, 'familyID')
      cust_name = lmc.getattribute('samples', sample, 'customer')
      if cust_name is None or not re.match(r'cust\d{3}', cust_name):
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

        # try to create old dir structure
        try:
          os.makedirs(os.path.join(outputdir, 'exomes', sample, 'fastq'))
        except OSError:
          pass

        # try to create new dir structure
        if cust_name != None and family_id != None:
          try:
            os.makedirs(os.path.join(outputdir, cust_name, family_id, 'exomes', sample, 'fastq'))
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
            sample_name=sample,
            fclane=fclane
          )
      else:                        # Otherwise just present the data
        print("{sample} FAIL with {readcount} M reads.\n"
              "Requested with {reqreadcount} M reads.\n"
              "These flowcells summarized {fclanes}".format(sample=sample, readcount=rc, fclanes=fclanes, reqreadcount=readcounts))
    else:
      print("{} - no analysis parameter specified in lims".format(sample))

if __name__ == '__main__':
  main(sys.argv[1:])
