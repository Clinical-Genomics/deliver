#!/usr/bin/python
#

from __future__ import print_function
import sys
import glob
import re
import os
import os.path
import grp
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '1.6.1'

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

def get_fastq_files(demuxdir, fclane, sample_name):
    fastqfiles = glob.glob(
        "{demuxdir}*{fc}/Unalign*/Project_*/Sample_{sample_name}_*/*L00{lane}*gz".format(
          demuxdir=demuxdir, fc=fclane['fc'], sample_name=sample_name, lane=fclane['lane']
        ))
    fastqfiles.extend(glob.glob(
        "{demuxdir}*{fc}/Unalign*/Project_*/Sample_{sample_name}[BF]_*/*L00{lane}*gz".format(
          demuxdir=demuxdir, fc=fclane['fc'], sample_name=sample_name, lane=fclane['lane']
        )))

    return fastqfiles

def make_link(fastqfiles, outputdir, sample_name, fclane, link_type='soft'):
    for fastqfile in fastqfiles:
        nameparts = fastqfile.split("/")[-1].split("_")

        # X stuff
        undetermined = ''
        if nameparts[1] == 'Undetermined':
          undetermined = '-Undetermined'

        tile = ''
        if '-' in nameparts[0]:
          tile = nameparts[0].split('-')[1].split('t')[1] # H2V2YCCXX-l2t21
          tile = '-' + tile

        rundir = fastqfile.split("/")[6]
        date = rundir.split("_")[0]
        newname = "{lane}_{date}_{fc}{tile}{undetermined}_{sample_name}_{index}_{readdirection}.fastq.gz".format(
            lane=fclane['lane'],
            date=date,
            fc=fclane['fc'],
            sample_name=sample_name,
            index=nameparts[-4],
            readdirection=nameparts[-2][-1:],
            undetermined=undetermined,
            tile=tile
        )

        # first remove the link - might be pointing to wrong file
        dest_fastqfile = os.path.join(outputdir, newname)
        try:
            os.remove(dest_fastqfile)
        except OSError:
            pass

        # then create it
        try:
            if link_type == 'soft':
                print("ln -s {} {} ...".format(fastqfile, dest_fastqfile))
                os.symlink(fastqfile, dest_fastqfile)
            else:
                print("ln {} {} ...".format(os.path.realpath(fastqfile), dest_fastqfile))
                os.link(os.path.realpath(fastqfile), dest_fastqfile)
                os.chmod(dest_fastqfile, 0o644)
                gid = grp.getgrnam("users").gr_gid
                os.chown(dest_fastqfile, -1, gid)
        except:
            print("Can't create symlink for {} in {}".format(sample_name, os.path.join(outputdir, newname)))

def main(argv):

  print('Version: {} {}'.format(__file__, __version__))

  outbasedir = '/mnt/hds/proj/'
  outputdir = 'bioinfo/MIP_ANALYSIS/'

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

  params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
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
    seq_type_dir = 'exomes'
    q30_cutoff = 80

    try:
      family_id = sample.udf['familyID']
    except KeyError:
      family_id = None
    try:
      cust_name = sample.udf['customer']
      if cust_name is not None:
        cust_name = cust_name.lower()
    except KeyError:
      cust_name = 'cust000'
    if family_id == None and analysistype != None:
      print("ERROR '{}' family_id is not set".format(sample_id))
      continue

    try:
      cust_sample_name = sample.name
    except AttributeError:
      print("WARNING '{}' does not have a customer sample name".format(sample_id))
      cust_sample_name=sample_id

    dbinfo = getsampleinfofromname(params, sample_id)
    print(dbinfo)
    rc = 0         # counter for total readcount of sample
    fclanes = []   # list to keep flowcell names and lanes for a sample
    for info in dbinfo:
      if analysistype == None or info['q30'] > q30_cutoff:     # Use readcount from lane only if it satisfies QC [=80%]
        rc += info['M_reads']
        fclanes.append(dict(( (key, info[key]) for key in ['fc', 'q30', 'lane'] )))
      else:
        print("WARNING: '{sample_id}' did not reach Q30 > {cut_off} for {flowcell}".format(sample_id=sample_id, cut_off=q30_cutoff, flowcell=info['fc']))

    # create the customer folders and links regardless of the QC
    try:
      os.makedirs(os.path.join(outbasedir, cust_name, 'INBOX', seq_type_dir, cust_sample_name))
    except OSError:
      pass
    # create symlinks for each fastq file
    for fclane in fclanes:
      fastqfiles = get_fastq_files(params['DEMUXDIR'], fclane, sample_id)
      make_link(
        fastqfiles=fastqfiles,
        outputdir=os.path.join(outbasedir, cust_name, 'INBOX', seq_type_dir, cust_sample_name),
        fclane=fclane,
        sample_name=cust_sample_name,
        link_type='hard'
      )

if __name__ == '__main__':
  main(sys.argv[1:])
