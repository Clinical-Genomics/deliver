# -*- coding: utf-8 -*-
import logging

from access import db
from deliver.exc import MissingFastqFilesError

logger = logging.getLogger(__name__)


def getsampleinfo(flowcell=None, lane=None, sample=None):
    db_params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    query = (" SELECT samplename, flowcellname AS flowcell, lane " +
             " FROM sample, unaligned, flowcell, demux " +
             " WHERE sample.sample_id = unaligned.sample_id AND unaligned.demux_id = demux.demux_id " +
             " AND demux.flowcell_id = flowcell.flowcell_id ")
    if sample:
        query += " AND (samplename LIKE '{sample}\_%' OR samplename = '{sample}' OR samplename LIKE '{sample}B\_%' OR samplename LIKE '{sample}F\_%')".format(sample=sample)

    if flowcell:
        query += " AND flowcellname = '{flowcell}'".format(flowcell=flowcell)

    if lane:
        query += " AND lane = {lane}".format(lane=lane)

    with db.dbconnect(db_params['CLINICALDBHOST'], db_params['CLINICALDBPORT'], db_params['STATSDB'], db_params['CLINICALDBUSER'], db_params['CLINICALDBPASSWD']) as dbc:
       replies = dbc.generalquery( query )
    return replies


