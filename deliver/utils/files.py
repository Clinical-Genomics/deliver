# -*- coding: utf-8 -*-

import grp
import logging

from path import path


logger = logging.getLogger(__name__)


def get_mipname(fastq_file):
    """Takes a demux fastq file and returns a MIP compatible fastq file

    Args:
        fastq_file (str): a FQP to a fastq file.

    Returns (str): A MIP compatible fastq file.
    """
    dirparts = fastq_file.split("/")
    nameparts = dirparts[-1].split("_")

    # H3LGFCCXX-l1t21_973470_CGGCTATG_L001_R2_001.fastq.gz
    # H3LGFCCXX-l1t21_Undetermined_CGGCTATG_L001_R1_001.fastq.gz

    index = nameparts[2]
    fc = dirparts[-5].split("_")[-1][1:] # no worries, this'll always work, right?
    lane = int(nameparts[-3][-1:])
    readdirection=nameparts[-2][-1:]
    rundir = dirparts[-5]
    date = rundir.split("_")[0]
    sample_id = dirparts[-2].split("_")[1]

    # X stuff
    undetermined = ''
    if nameparts[1] == 'Undetermined':
        undetermined = '-Undetermined'

    tile = ''
    if '-' in nameparts[0]:
        tile = nameparts[0].split('-')[1].split('t')[1] # H2V2YCCXX-l2t21
        tile = '-' + tile

    newname = "{lane}_{date}_{fc}{tile}{undetermined}_{sample}_{index}_{readdirection}.fastq.gz".format(
        lane=lane,
        date=date,
        fc=fc,
        sample=sample_id,
        index=index,
        readdirection=readdirection,
        undetermined=undetermined,
        tile=tile
    )

    return newname


def make_link(source, dest, link_type='hard'):
    path(dest).remove_p()

    try:
        if link_type == 'soft':
            logger.debug("ln -s {} {} ...".format(source, dest))
            path(source).symlink(dest)
        else:
            real_source = path(source).realpath()
            logger.debug("ln {} {} ...".format(real_source, dest))
            path(real_source).link(dest)
            path(dest).chmod(0o644)
            gid = grp.getgrnam("users").gr_gid
#            path(dest).chown(-1, gid)
    except Exception, e: # catch, print, and continue
        logger.error(repr(e))
        return False

    return True
