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

def make_link(demuxdir, outputdir, family_id, cust_name, sample_name, fclane):
      fastqfiles = glob.glob(
        "{demuxdir}*{fc}*/Unalign*/Project_*/Sample_*{sample_name}[BF]_*/*L00{lane}*gz".format(
          demuxdir=demuxdir, fc=fclane[0], sample_name=sample_name, lane=fclane[2]
        ))
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
    print(sample)
    family_id = None
    cust_name = None
    with lims.limsconnect(params['apiuser'], params['apipass'], params['baseuri']) as lmc:
      analysistype = lmc.getattribute('samples', sample, "Sequencing Analysis")
      readcounts = .75 * float(analysistype[-3:])    # Accepted readcount is 75% of ordered million reads
      family_id = lmc.getattribute('samples', sample, 'familyID')
      cust_name = lmc.getattribute('samples', sample, 'customer')
      if not re.match(r'cust\d{3}', cust_name):
        print("'{}' does not match an internal customer name".format(cust_name))
        cust_name = None
    dbinfo = getsampleinfofromname(params, sample)
    rc = 0         # counter for total readcount of sample
    fclanes = {}   # dict to keep flowcell names and lanes for a sample
    cnt = 0        # counter used in the dict to keep folwcell/lane count
    for info in dbinfo:
      if (info['q30'] > 80):     # Use readcount from lane only if it satisfies QC [=80%]
        cnt += 1
        rc += info['M_reads']
        fclanes[cnt] = "{info[fc]}_{info[q30]}_{info[lane]}".format(info=info)
    if readcounts:
      if (rc > readcounts):        # If enough reads are obtained do
        print("{sample} Passed {readcount} M reads\nUsing reads from {fclanes}".format(sample=sample, readcount=rc, fclanes=fclanes))
        try:
          os.makedirs(os.path.join(outputdir, 'exomes', sample, 'fastq'))
        except OSError:
          pass
        for entry in fclanes.values():
          fclane = entry.split("_")
          make_link(
            demuxdir=params['DEMUXDIR'],
            outputdir=outputdir,
            family_id=family_id,
            cust_name=cust_name,
            sample_name=sample,
            fclane=fclane
          )
      else:                        # Otherwise just present the data
        print("{sample} Fail {readcount} M reads" +
              "These flowcells summarized {fclanes}".format(sample=sample, readcount=rc, fclanes=fclanes))
    else:
      print("{} - no analysis parameter specified in lims".format(sample))

if __name__ == '__main__':
  main(sys.argv[1:])
