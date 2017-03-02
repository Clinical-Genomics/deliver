#!/usr/bin/python
#

from __future__ import print_function
import sys
import glob
import re
import logging

from path import Path

from cglims.apptag import ApplicationTag
from cglims.api import ClinicalSample
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

from ..utils import get_mipname, make_link

log = logging.getLogger(__name__)

db_params = []


def getsamplesfromflowcell(demuxdir, flowcell):
    fc_samples = {}
    demuxdir_glob = "{demuxdir}*{flowcell}/".format(demuxdir=demuxdir, flowcell=flowcell)

    if not glob.glob(demuxdir_glob):
        log.error('Directory not found: {}'.format(demuxdir_glob))
        return fc_samples

    samples = glob.glob("{demuxdir}*{flowcell}/Unalign*/Project_*/Sample_*"
                        .format(demuxdir=demuxdir, flowcell=flowcell))
    for sample in samples:
        sample = sample.split("/")[-1].split("_")[1]
        # remove reprep (B) and reception control fail (F) letters from
        # the samplename
        sample = sample.rstrip('BF')
        fc_samples[sample] = ''
    return fc_samples


def getsampleinfo(flowcell=None, lane=None, sample=None):
    global db_params
    if not db_params:
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


def getsampleinfofromname(sample):
    global db_params
    query = (" SELECT sample.sample_id AS id, samplename, flowcellname AS fc, " +
             " lane, ROUND(readcounts/2000000,2) AS M_reads, " +
             " ROUND(q30_bases_pct,2) AS q30, ROUND(mean_quality_score,2) AS score " +
             " FROM sample, unaligned, flowcell, demux " +
             " WHERE sample.sample_id = unaligned.sample_id AND unaligned.demux_id = demux.demux_id " +
             " AND demux.flowcell_id = flowcell.flowcell_id " +
             " AND (samplename LIKE '{sample}\_%' OR samplename = '{sample}' OR samplename LIKE '{sample}B\_%' OR samplename LIKE '{sample}F\_%')".format(sample=sample))
    with db.dbconnect(db_params['CLINICALDBHOST'], db_params['CLINICALDBPORT'], db_params['STATSDB'], db_params['CLINICALDBUSER'], db_params['CLINICALDBPASSWD']) as dbc:
       replies = dbc.generalquery( query )
    return replies


def getsampleinfofromname_glob(fc, demuxdir, sample):
    samples = glob.glob("{demuxdir}/*/Unalign*/Project_*/Sample_{sample}*/*fastq.gz"
                        .format(demuxdir=demuxdir, sample=sample))

    replies = []
    lanes = set()
    for sample in samples:
        sample_split = sample.split("/")[-1].split("_")
        lane = int(sample_split[3][1:])
        lanes.add(lane)

    for lane in lanes:
        replies.append({'fc': fc, 'lane': lane})

    return replies


def is_pooled_lane(flowcell, lane):
    global db_params
    if not db_params:
        db_params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    q = ("SELECT count(samplename) AS sample_count "
        "FROM sample "
        "JOIN unaligned ON sample.sample_id = unaligned.sample_id "
        "JOIN demux ON unaligned.demux_id = demux.demux_id "
        "JOIN flowcell ON demux.flowcell_id = flowcell.flowcell_id "
        "WHERE "
        "lane = {lane} and flowcell.flowcellname = '{flowcell}'".format(lane=lane, flowcell=flowcell))
    with db.dbconnect(db_params['CLINICALDBHOST'], db_params['CLINICALDBPORT'], db_params['STATSDB'], db_params['CLINICALDBUSER'], db_params['CLINICALDBPASSWD']) as dbc:
       replies = dbc.generalquery(q)
    return True if int(replies[0]['sample_count']) > 1 else False


def get_fastq_files(demuxdir, fc='*', lane='?', sample_name='*'):
    fastqfiles = glob.glob(
        "{demuxdir}*{fc}/Unalign*/Project_*/Sample_{sample_name}_*/*L00{lane}*fastq.gz".format(
          demuxdir=demuxdir, fc=fc, sample_name=sample_name, lane=lane
        ))
    fastqfiles.extend(glob.glob(
        "{demuxdir}*{fc}/Unalign*/Project_*/Sample_{sample_name}/*L00{lane}*fastq.gz".format(
          demuxdir=demuxdir, fc=fc, sample_name=sample_name, lane=lane
        )))
    fastqfiles.extend(glob.glob(
        "{demuxdir}*{fc}/Unalign*/Project_*/Sample_{sample_name}[BF]_*/*L00{lane}*fastq.gz".format(
          demuxdir=demuxdir, fc=fc, sample_name=sample_name, lane=lane
        )))

    if not fastqfiles:
        log.error("No fastq files found for {} on FC {} on lane {}"
                  .format(sample_name, fc, lane))

    return fastqfiles


def analysis_cutoff(analysis_type):
    """Based on the analysis type (exomes|genomes), return the q30 cutoff

    Args:
        analysis_type (str): exomes or genomes.

    Returns: returns the q30 cutoff in percent.

    """
    if analysis_type == 'wes':
        return 80
    if analysis_type == 'wgs':
        return 75

    # not recognized, cutoff 0
    return 0


def demux_links(fc, custoutdir, mipoutdir, demuxdir, force, skip_undetermined):
    """Link FASTQ files from DEMUX output of a flowcell."""

    global db_params
    db_params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    samples = getsamplesfromflowcell(demuxdir, fc)

    if not samples:
        log.error('No samples found for {}'.format(fc))
        exit(1)

    for sample_id in samples.iterkeys():
        family_id = None
        cust_name = None

        try:
            sample = Sample(lims, id=sample_id)
            sample.get(force=True)
        except:
            try:
                # maybe it's an old CG ID
                sample = lims.get_samples(udf={'Clinical Genomics ID': sample_id})[0]
                log.debug("Found as CG id in LIMS: {}!".format(sample_id))
            except:
                log.error("{} Skipping! Not found in LIMS.".format(sample_id))
                continue

        clinical_sample = ClinicalSample(sample)
        application_tag = clinical_sample.apptag

        if clinical_sample.pipeline == 'mwgs':
            log.info("skipping microbial sample: {}".format(sample_id))
            continue

        log.debug('Application tag: {}'.format(application_tag))

        requested_reads = application_tag.reads / 1000000
        seq_type = application_tag.sequencing

        # Accepted readcount is 75% of ordered million reads
        readcounts = .75 * float(requested_reads)
        raw_apptag = sample.udf['Sequencing Analysis']
        apptag = ApplicationTag(raw_apptag)
        seq_type_dir = apptag.analysis_type  # get wes|wgs
        q30_cutoff = analysis_cutoff(seq_type_dir)

        try:
            cust_name = sample.udf['customer']
            if cust_name is not None:
                cust_name = cust_name.lower()
        except KeyError:
            cust_name = None
        if cust_name is None:
            log.error("'{}' internal customer name is not set".format(sample_id))
            continue
        elif not re.match(r'cust\d{3}', cust_name):
            log.error("'{}' does not match an internal customer name".format(cust_name))
            continue

        try:
            # make sure there no "/" in customer sample name
            cust_sample_name = (sample.name.replace("/", "-") if "/" in
                                sample.name else sample.name)
        except AttributeError:
            log.warn("'{}' does not have a customer sample name".format(sample_id))
            cust_sample_name = sample_id

        if force:
            fclanes = getsampleinfofromname_glob(fc, demuxdir, sample_id)
            log.debug(fclanes)
        else:
            dbinfo = getsampleinfofromname(sample_id)
            log.debug(dbinfo)
            rc = 0         # counter for total readcount of sample
            fclanes = []   # list to keep flowcell names and lanes for a sample
            for info in dbinfo:
                # Use readcount from lane only if it satisfies QC [=80%]
                if info['q30'] > q30_cutoff:
                    rc += info['M_reads']
                    fclanes.append(dict(( (key, info[key]) for key in ['fc', 'q30', 'lane'] )))
                else:
                    log.warn("'{sample_id}' did not reach Q30 > {cut_off} for {flowcell}".format(sample_id=sample_id, cut_off=q30_cutoff, flowcell=info['fc']))

        # check the family id
        try:
            family_id = sample.udf['familyID']
        except KeyError:
            family_id = None
        if family_id == None and seq_type != 'RML':
            log.error("'{}' family_id is not set".format(sample_id))
            continue

        # create the links for the analysis
        if readcounts:
            if force or rc > readcounts: # If enough reads are obtained do
                # try to create new dir structure
                sample_outdir = Path(mipoutdir).joinpath(cust_name, family_id, seq_type_dir, sample_id, 'fastq')
                Path(sample_outdir).makedirs_p()

                # create symlinks for each fastq file
                link_results = {} # { fc: # of link }
                for fclane in fclanes:
                    if fclane['fc'] not in link_results:
                        link_results[fclane['fc']] = 0

                    fastqfiles = get_fastq_files(demuxdir, fclane['fc'], fclane['lane'], sample_id)

                    for fastqfile in fastqfiles:
                        # skip undeermined for pooled samples
                        if 'Undetermined' in fastqfile:
                            if skip_undetermined or is_pooled_lane(fclane['fc'], fclane['lane']):
                                log.info('Skipping pooled undetermined indexes!')
                                continue

                        outfile = get_mipname(fastqfile)
                        outfile = Path(sample_outdir).joinpath(outfile)

                        link_rs = make_link(
                            fastqfile,
                            outfile,
                            link_type='soft'
                        )

                        if link_rs:
                            link_results[fclane['fc']] += 1

                link_results_str = ', '.join([ "{} ({} files)".format(fc, files) for fc, files in link_results.items() ])
                log.info("Linked {} from {}".format(sample_id, link_results_str))

            else:                        # Otherwise just present the data
                log.error("{sample_id} FAIL with {readcount} M reads.\n"
                          "Requested with {reqreadcount} M reads.\n"
                          "These flowcells summarized {fclanes}"
                          .format(sample_id=sample_id, readcount=rc,
                                  fclanes=fclanes, reqreadcount=readcounts))
        else:
            log.error("{} - no analysis parameter specified in lims".format(sample_id))


if __name__ == '__main__':
    main(sys.argv[1:])
