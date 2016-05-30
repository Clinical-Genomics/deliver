#!/usr/bin/python

from __future__ import print_function
import sys
import os
import logging
import re
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '1.9.0'

logger = logging.getLogger(__name__)

class ExternalIDNotFoundException(Exception):
    pass

def get_internal_id(external_id):
    """ Looks up the internal sample ID from an external ID in LIMS
    args:
        external_id (str): external sample ID

    return (str, None): internal sample ID or None
    """

    params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    try:
        samples = lims.get_samples(name=external_id)

        # multiple samples could be returned, get the latest one
        samples.sort(key=lambda x: x.date_received, reverse=True)

        return samples[0].id
    except:
        logger.error("External ID '{}' was not found in LIMS".format(external_id))
        raise ExternalIDNotFoundException("External ID '{}' was not found in LIMS".format(external_id))

    return None

def make_link(source, dest, link_type='hard'):
    # remove previous link
    try:
        os.remove(dest)
    except OSError:
        pass

    # then create it
    try:
        if link_type == 'soft':
            logger.info("ln -s {} {} ...".format(source, dest))
            os.symlink(source, dest)
        else:
            logger.info("ln {} {} ...".format(os.path.realpath(source), dest))
            os.link(os.path.realpath(source), dest)
    except:
        logger.error("Can't create symlink from {} to {}".format(source, dest))

def setup_logging(level='INFO'):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # customize formatter, align each column
    template = "[%(asctime)s] %(name)-25s %(levelname)-8s %(message)s"
    formatter = logging.Formatter(template)

    # add a basic STDERR handler to the logger
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)

    root_logger.addHandler(console)
    return root_logger

def cust_links(fastq_full_file_name, outdir):

    logger.info('Version: {} {}'.format(__file__, __version__))
    #outdir = '/mnt/hds/proj/bioinfo/EXTERNAL/'

    fastq_file_name = os.path.basename(fastq_full_file_name)
    fastq_file_name_split = fastq_file_name.split('_')
    direction, extension = fastq_file_name_split[-1].split('.', 1)

    # standard values
    FC = None
    lane  = '1'
    date  = '0'
    FC    = '0'
    index = '0'
    direction = str(int(direction)) # easy way of removing leading zero's

    # four formats: external-id_direction, lane_external-id_direction, LANE_DATE_FC_SAMPLE_INDEX_DIRECTION, SAMPLE_FC_LANE_DIRECTION_PART
    if len(fastq_file_name_split) == 2:
        logger.info('Found SAMPLE_DIRECTION format: {}'.format(fastq_file_name))

        external_id = fastq_file_name_split[:-1]
    elif len(fastq_file_name_split) == 3:
        logger.info('Found LANE_SAMPLE_DIRECTION format: {}'.format(fastq_file_name))

        lane  = fastq_file_name_split[0]
        external_id = fastq_file_name_split[1:-1]
    elif len(fastq_file_name_split) == 6:
        logger.info('Found LANE_DATE_FC_SAMPLE_INDEX_DIRECTION format: {}'.format(fastq_file_name))

        date  = fastq_file_name_split[1]
        FC    = fastq_file_name_split[2]
        index = fastq_file_name_split[4]
        lane  = fastq_file_name_split[0]
        external_id = fastq_file_name_split[3]
    elif len(fastq_file_name_split) == 5:
        m = re.match(r'(.*?)_(.*?)_L(\d+)_R(\d+)_(\d+)', fastq_file_name)
        if m:
            logger.info('Found SAMPLE_FC_LANE_DIRECTION_PART format: {}'.format(fastq_file_name))

            if not re.match(r'S\d', m.group(2)):
                FC = m.group(2)
            lane  = str(int(m.group(3)))
            external_id = m.group(1)
            direction = m.group(4)

    internal_id = get_internal_id(external_id)

    out_file_name = '_'.join([lane, date, FC, internal_id, index, direction])
    out_file_name = '{}.{}'.format(out_file_name, extension)
    print(out_file_name)
    exit()

    # make out dir
    complete_outdir = os.path.join(outdir, internal_id)
    if not os.path.isdir(complete_outdir):
        try:
            logger.info('mkdir -p ' + complete_outdir)
            os.makedirs(complete_outdir)
        except OSError:
            logger.error('Failed to create {}'.format(complete_outdir))
            exit()

    # link!
    make_link(
        fastq_full_file_name,
        os.path.join(complete_outdir, out_file_name),
        'hard'
    )

if __name__ == '__main__':
    setup_logging('DEBUG')
    main(sys.argv[1:])
