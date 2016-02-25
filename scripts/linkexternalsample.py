#!/usr/bin/python

from __future__ import print_function
import sys
import os
import logging
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '1.7.0'

logger = logging.getLogger(__name__)

def get_internal_id(external_id):
    """ Looks up the internal sample ID from an external ID in LIMS
    args:
        external_id (str): external sample ID
    
    return (str, None): internal sample ID or None
    """
    
    params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    try:
        sample = lims.get_samples(name=external_id)
        return sample[0].id
    except:
        logger.error("External ID '{}' was not found in LIMS".format(external_id))

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
            logging.info("ln -s {} {} ...".format(source, dest))
            os.symlink(source, dest)
        else:
            logging.info("ln {} {} ...".format(os.path.realpath(source), dest))
            os.link(os.path.realpath(source), dest)
    except:
        logging.error("Can't create symlink from {} to {}".format(source, dest))

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

def main(argv):

    logger.info('Version: {} {}'.format(__file__, __version__))
    
    outdir = '/mnt/hds/proj/bioinfo/EXTERNAL/'
  
    if len(argv) > 0:
        try:
            argv[0]
        except NameError:
            sys.exit("Usage: {} <full path to fastq file>".format(__file__))
        else:
            fastq_full_file_name = argv[0]
    else:
        sys.exit("Usage: {} <full path to fastq file>".format(__file__))
  
    fastq_file_name = os.path.basename(fastq_full_file_name)
    fastq_file_name_split = fastq_file_name.split('_')

    # two formats: external-id_direction and lane_external-id_direction
    if len(fastq_file_name_split) == 2:
        lane = '1'
        # make the external id more idiot proof by slicing off direction
        external_id = fastq_file_name_split[:-1]
    if len(fastq_file_name_split) == 3:
        lane = fastq_file_name_split[0]
        # make the external id more idiot proof by slicing off lane and direction
        external_id = fastq_file_name_split[1:-1]

    direction = fastq_file_name_split[-1] # will also have the ext
    internal_id = get_internal_id(external_id)

    complete_outdir = os.path.join(outdir, internal_id)
    try:
        logging.info('mkdir -p ' + complete_outdir)
        os.makedirs(complete_outdir)
    except OSError:
        logging.warning('Failed to create {}'.format(complete_outdir))
    finally:
        make_link(
            fastq_full_file_name,
            os.path.join(complete_outdir, '_'.join( [lane, internal_id, direction ])),
            'hard'
        )

if __name__ == '__main__':
    setup_logging('DEBUG')
    main(sys.argv[1:])
