#!/usr/bin/python

from __future__ import print_function
import sys
import os
import logging
import re
import gzip
import time

from cglims.apptag import ApplicationTag

from access import db
from datetime import datetime
from glob import glob
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '1.9.0'

logger = logging.getLogger(__name__)

def get_sample(sample_id):
    """ Looks up the internal sample ID from an external ID in LIMS
    args:
        external_id (str): external sample ID

    return (str, None): internal sample ID or None
    """
    params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    try:
        sample = Sample(lims, id=sample_id)
        sample.get(force=True)
        return sample
    except:
        logger.error("Sample '{}' was not found in LIMS".format(sample_id))

    return None

def make_link(source, dest, link_type='hard'):
    # remove previous link
    #try:
    #    os.remove(dest)
    #except OSError:
    #    pass

    # then create it
    try:
        if link_type == 'soft':
            logger.info("ln -s {} {} ...".format(source, dest))
            os.symlink(source, dest)
        else:
            logger.info("ln {} {} ...".format(os.path.realpath(source), dest))
            os.link(os.path.realpath(source), dest) # make sure to link to orignal file, not a symlink
    except:
        logger.error("Can't create symlink from {} to {}".format(source, dest))

def get_family_id(sample):
    try:
        family_id = sample.udf['familyID']
    except KeyError:
        family_id = None

    return family_id

def get_cust_name(sample):
    try:
        cust_name = sample.udf['customer']
        if cust_name is not None:
            cust_name = cust_name.lower()
    except KeyError:
        logger.error("'{}' internal customer name is not set".format(sample.id))
        return None

    if not re.match(r'cust\d{3}', cust_name):
        logger.error("'{}' does not match an internal customer name".format(cust_name))
        return None

    return cust_name

def get_index(fastq_file_name):
    with gzip.open(fastq_file_name, 'rb') as f:
        line = f.readline().rstrip()
        while not line.startswith('@'):
            line = f.readline().rstrip()

        index = line.split(':')[-1]

        if '#' in index: # possible early fastq header line
            # @HWUSI-EAS100R:6:73:941:1973#0/1
            m = re.search(r'.*#(.+)/.*', index)
            if m:
                index = m.group(1)

        return index

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

def ext_links(start_dir, outdir):

    logger.info('Version: {} {}'.format(__file__, __version__))

    for fastq_full_file_name in glob(os.path.join(start_dir, '*fastq.gz')):
        fastq_file_name = os.path.basename(fastq_full_file_name)
        fastq_file_name_split = fastq_file_name.split('_')

        # get info from the sample file name
        lane = fastq_file_name_split[0]
        direction = fastq_file_name_split[-1] # will also have the ext
        sample_id = fastq_file_name_split[3]
        index = fastq_file_name_split[4]
        FC = fastq_file_name_split[2]
        if FC == '0':
            FC = 'EXTERNALX'

        # get info from LIMS
        sample = get_sample(sample_id)
        family_id = get_family_id(sample)
        cust_name = get_cust_name(sample)
        raw_apptag = sample.udf['Sequencing Analysis']
        apptag = ApplicationTag(raw_apptag)
        seq_type_dir = apptag.analysis_type # get wes|wgs
        if sample.date_received is not None:
            date = datetime.strptime(sample.date_received, "%Y-%m-%d").strftime("%y%m%d")
        else:
            mtime = os.path.getmtime(fastq_full_file_name)
            date = time.strftime("%y%m%d", time.localtime(mtime))

        # some more info
        if index == '0':
            index = get_index(fastq_full_file_name)

        # create dest dir
        complete_outdir = os.path.join(outdir, cust_name, family_id, seq_type_dir, sample_id, 'fastq')
        out_filename = '_'.join( [lane, date, FC, sample_id, index, direction ])
        out_full_filename = os.path.join(complete_outdir, out_filename)
        logger.debug(complete_outdir)
        logger.debug(out_filename)

        # check if file already exists
        if os.path.isfile(out_full_filename):
            logger.info('Skipping creation of {}. Already exists'.format(out_full_filename))
            continue

        # create the out dir
        if not os.path.isdir(complete_outdir):
            try:
                logger.info('mkdir -p ' + complete_outdir)
                os.makedirs(complete_outdir)
            except OSError:
                logger.warning('Failed to create {}'.format(complete_outdir))
                exit()

        # link!
        make_link(
            fastq_full_file_name,
            out_full_filename,
            'soft'
        )

if __name__ == '__main__':
    setup_logging('DEBUG')
    main(sys.argv[1:])
