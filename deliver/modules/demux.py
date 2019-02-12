"""Get information from cgstats"""

from __future__ import print_function
import glob
import logging

LOG = logging.getLogger(__name__)

def getsampleinfo(cursor, flowcell=None, lane=None, sample=None):
    """Get flowcell and lane from a sample"""

    query = (" SELECT samplename, flowcellname AS flowcell, lane "
             " FROM sample, unaligned, flowcell, demux "
             " WHERE sample.sample_id = unaligned.sample_id"
             " AND unaligned.demux_id = demux.demux_id "
             " AND demux.flowcell_id = flowcell.flowcell_id ")
    if sample:
        query += " AND (samplename LIKE '{sample}\_%' " \
                 " OR samplename = '{sample}' " \
                 " OR samplename LIKE '{sample}B\_%' " \
                 " OR samplename LIKE '{sample}F\_%')".format(sample=sample)

    if flowcell:
        query += " AND flowcellname = '{flowcell}'".format(flowcell=flowcell)

    if lane:
        query += " AND lane = {lane}".format(lane=lane)

    replies = cursor.query(query)
    return replies


def is_pooled_lane(cursor, flowcell, lane):
    query = ("SELECT count(samplename) AS sample_count "
             "FROM sample "
             "JOIN unaligned ON sample.sample_id = unaligned.sample_id "
             "JOIN demux ON unaligned.demux_id = demux.demux_id "
             "JOIN flowcell ON demux.flowcell_id = flowcell.flowcell_id "
             "WHERE "
             "lane = {lane} and flowcell.flowcellname = '{flowcell}'"
             .format(lane=lane, flowcell=flowcell))
    replies = cursor.query(query)
    return True if int(replies[0]['sample_count']) > 1 else False


def get_fastq_files(demuxdir, fc='*', lane='?', sample_name='*'):
    fastqfiles = glob.glob(
        "{demuxdir}/*{fc}/Unalign*/Project_*/Sample_{sample_name}_*/*L00{lane}*fastq.gz".format(
            demuxdir=demuxdir, fc=fc, sample_name=sample_name, lane=lane
        ))
    fastqfiles.extend(glob.glob(
        "{demuxdir}/*{fc}/Unalign*/Project_*/Sample_{sample_name}/*L00{lane}*fastq.gz".format(
            demuxdir=demuxdir, fc=fc, sample_name=sample_name, lane=lane
        )))
    fastqfiles.extend(glob.glob(
        "{demuxdir}/*{fc}/Unalign*/Project_*/Sample_{sample_name}[BF]_*/*L00{lane}*fastq.gz".format(
            demuxdir=demuxdir, fc=fc, sample_name=sample_name, lane=lane
        )))

    if not fastqfiles:
        LOG.error("No fastq files found for %s on FC %s on lane %s", sample_name, fc, lane)

    return fastqfiles
