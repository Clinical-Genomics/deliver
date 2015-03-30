#!/usr/bin/python
#
import sys
from access import db

"""Summarize read counts for sample on flowcell and generat.
  usage: create fastqln.py <flowcell> <config_file:optional>"
Args:
  flowcell (str): name of flowcell in database
Returns:
  str: summary for each sample in project on flowcell [stored in database]
"""

if (len(sys.argv)>3):
  configfile = sys.argv[3]
else:
  configfile = 'None'
pars = db.readconfig(configfile)

with db.create_tunnel(pars['TUNNELCMD']):

  with db.dbconnect(pars['CLINICALDBHOST'], pars['CLINICALDBPORT'], pars['STATSDB'], 
                        pars['CLINICALDBUSER'], pars['CLINICALDBPASSWD']) as dbc:

    ver = dbc.versioncheck(pars['STATSDB'], pars['DBVERSION'])

    if not ver == 'True':
      print "Wrong db " + pars['STATSDB'] + " v:" + pars['DBVERSION']
      exit(0) 
    else:
      print "Correct db " + pars['STATSDB'] + " v:" + pars['DBVERSION']

