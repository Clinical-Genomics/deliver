#!/usr/bin/python
#

from __future__ import print_function
import sys
import glob
import re
import grp
import logging

from path import path

from cglims.apptag import ApplicationTag
from cglims.api import ClinicalSample
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

log = logging.getLogger(__name__)

db_params = []

def getsamplesfromflowcell(demuxdir, flwc):
    samples = glob.glob("{demuxdir}*{flowcell}/Unalign*/Project_*/Sample_*"
                        .format(demuxdir=demuxdir, flowcell=flwc))
    fc_samples = {}
    for sample in samples:
        sample = sample.split("/")[-1].split("_")[1]
        # remove reprep (B) and reception control fail (F) letters from
        # the samplename
        sample = sample.rstrip('BF')
        fc_samples[sample] = ''
    return fc_samples


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
        replies.append( { 'fc': fc, 'lane': lane } )

    return replies

def is_pooled_sample(flowcell, lane):
    global db_params
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


def make_link(fastqfiles, outputdir, sample_name, fclane, link_type='soft', skip_undetermined=False):
    for fastqfile in fastqfiles:
        nameparts = fastqfile.split("/")[-1].split("_")

        # X stuff
        undetermined = ''
        if nameparts[1] == 'Undetermined':
            # skip undeermined for pooled samples
            if skip_undetermined or is_pooled_sample(fclane['fc'], fclane['lane']):
                log.info('Skipping pooled undetermined indexes!')
                continue
            undetermined = '-Undetermined'

        tile = ''
        if '-' in nameparts[0]:
            tile = nameparts[0].split('-')[1].split('t')[1] # H2V2YCCXX-l2t21
            tile = '-' + tile

        rundir = fastqfile.split("/")[6]
        date = rundir.split("_")[0]

        newname = "{lane}_{date}_{fc}{tile}{undetermined}_{sample}_{index}_{readdirection}.fastq.gz".format(
            lane=fclane['lane'],
            date=date,
            fc=fclane['fc'],
            sample=sample_name,
            index=nameparts[-4],
            readdirection=nameparts[-2][-1:],
            undetermined=undetermined,
            tile=tile
        )

        # first remove the link - might be pointing to wrong file
        dest_fastqfile = path(outputdir).joinpath(newname)
        path(dest_fastqfile).remove_p()

        # then create it
        try:
            if link_type == 'soft':
                log.debug("ln -s {} {} ...".format(fastqfile, dest_fastqfile))
                path(fastqfile).symlink(dest_fastqfile)
            else:
                fastqfile_realpath = path(fastqfile).realpath()
                log.debug("ln {} {} ...".format(fastqfile_realpath, dest_fastqfile))
                path(fastqfile_realpath).link(dest_fastqfile)
                path(dest_fastqfile).chmod(0o644)
                gid = grp.getgrnam("users").gr_gid
                path(dest_fastqfile).chown(-1, gid)
        except:
            log.error("Can't create symlink for {} in {}".format(sample_name, dest_fastqfile))

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


def demux_links(fc, custoutdir, mipoutdir, force, skip_undetermined):
    """Link FASTQ files from DEMUX output of a flowcell."""

    global db_params
    db_params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    samples = getsamplesfromflowcell(db_params['DEMUXDIR'], fc)

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

        readcounts = .75 * float(requested_reads)    # Accepted readcount is 75% of ordered million reads
        raw_apptag = sample.udf['Sequencing Analysis']
        apptag = ApplicationTag(raw_apptag)
        seq_type_dir = apptag.analysis_type # get wes|wgs
        q30_cutoff = analysis_cutoff(seq_type_dir)

        try:
            cust_name = sample.udf['customer']
            if cust_name is not None:
                cust_name = cust_name.lower()
        except KeyError:
            cust_name = None
        if cust_name == None:
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
            fclanes = getsampleinfofromname_glob(fc, db_params['DEMUXDIR'], sample_id)
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

        # create the customer folders and links regardless of the QC
        cust_inbox_outdir = path(custoutdir).joinpath(cust_name, 'INBOX', seq_type_dir, cust_sample_name)
        path(cust_inbox_outdir).makedirs_p()
        # create symlinks for each fastq file
        for fclane in fclanes:
            fastqfiles = get_fastq_files(db_params['DEMUXDIR'], fclane, sample_id)
            make_link(
                fastqfiles=fastqfiles,
                outputdir=cust_inbox_outdir,
                fclane=fclane,
                sample_name=cust_sample_name,
                link_type='hard',
                skip_undetermined=skip_undetermined
            )

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
                if force:
                    log.info("{sample_id} Passed".format(sample_id=sample_id))
                else:
                    log.info("{sample_id} Passed {readcount} M reads\nUsing reads from {fclanes}".format(sample_id=sample_id, readcount=rc, fclanes=fclanes))

                # try to create new dir structure
                sample_outdir = path(mipoutdir).joinpath(cust_name, family_id, seq_type_dir, sample_id, 'fastq')
                path(sample_outdir).makedirs_p()

                # create symlinks for each fastq file
                for fclane in fclanes:
                    fastqfiles = get_fastq_files(db_params['DEMUXDIR'], fclane, sample_id)
                    make_link(
                        fastqfiles=fastqfiles,
                        outputdir=sample_outdir,
                        fclane=fclane,
                        sample_name=sample_id,
                        skip_undetermined=skip_undetermined
                    )
            else:                        # Otherwise just present the data
              log.error("{sample_id} FAIL with {readcount} M reads.\n"
                    "Requested with {reqreadcount} M reads.\n"
                    "These flowcells summarized {fclanes}".format(sample_id=sample_id, readcount=rc, fclanes=fclanes, reqreadcount=readcounts))
        else:
            log.error("{} - no analysis parameter specified in lims".format(sample_id))

if __name__ == '__main__':
    main(sys.argv[1:])
