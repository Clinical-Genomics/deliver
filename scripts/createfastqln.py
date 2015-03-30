#!/usr/bin/python
#
import sys
import glob
from access import db, lims

"""Summarize read counts for sample on flowcell and generat.
  usage: create fastqln.py <flowcell> <config_file:optional>"
Args:
  flowcell (str): name of flowcell in database
Returns:
  str: summary for each sample in project on flowcell [stored in database]
"""

if (len(sys.argv)>2):
  configfile = sys.argv[2]
else:
  configfile = 'None'
pars = db.readconfig(configfile)

fc_samples = {}
def getsamplesfromflowcell(flwc):
  samples = glob.glob(pars['DEMUXDIR'] + "*" + flwc + "*/Unalign*/Project_*/Sample_*")
  for sampl in samples:
    sample = sampl.split("/")[len(sampl.split("/"))-1].split("_")[1]
    fc_samples[sample] = ''
  return fc_samples

def getsampleinfofromname(sample):
  query = (""" SELECT sample.sample_id AS id, samplename, flowcellname AS fc, 
            lane, ROUND(readcounts/2000000,2) AS M_reads, 
            ROUND(q30_bases_pct,2) AS q30, ROUND(mean_quality_score,2) AS score 
            FROM sample, unaligned, demux, flowcell 
            WHERE sample.sample_id = unaligned.sample_id AND unaligned.demux_id = demux.demux_id 
            AND flowcell.flowcell_id = demux.flowcell_id  
            AND (samplename LIKE '""" + sample + """_%' OR samplename = '""" + sample + """')""")
  print query
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

with db.create_tunnel(pars['TUNNELCMD']):

  with db.dbconnect(pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], 
                        pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']) as dbc:
    print pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']

    ver = dbc.versioncheck(pars['STATSDB'], pars['DBVERSION'])

    if not ver == 'True':
      print "Wrong db " + pars['STATSDB'] + " v:" + pars['DBVERSION']
      exit(0) 
    else:
      print "Correct db " + pars['STATSDB'] + " v:" + pars['DBVERSION']

    flowc = sys.argv[1]

    smpls = getsamplesfromflowcell(flowc)

    for sample in smpls.iterkeys():
#    with lims.limsconnect(pars['apiuser'], pars['apipass'], pars['baseuri']) as lmc:
#      analysistype = lmc.getattribute('samples', sample, "Sequencing Analysis")
#      readcounts = .75 * float(analysistype[-3:])    # Accepted readcount is 75% of ordered million reads
      dbinfo = getsampleinfofromname(sample)
      rc = 0         # counter for total readcount of sample
      fclanes = {}   # dict to keep flowcell names and lanes for a sample
      cnt = 0        # counter used in the dict to keep folwcell/lane count
      for info in dbinfo:
        if (info['q30'] > 80):     # Use readcount from lane only if it satisfies QC [=80%]
          cnt += 1
          rc += info['M_reads']
          fclanes[cnt] = info['fc'] + "_" + str(info['q30']) + "_" + str(info['lane'])
#    if readcounts:
      if (rc > readcounts):        # If enough reads are obtained do
        print sample + " Passed " + str(rc) + " M reads\nUsing reads from " + str(fclanes)
        makelinks(sample, fclanes)
      else:                        # Otherwise just present the data
        print sample + " Fail " + str(rc) + " M reads\nThese flowcells summarixed " + str(fclanes)
#    else:
#      print sample + " - no analysis parameter specified in lims"
