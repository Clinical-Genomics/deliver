#!/usr/bin/python

from __future__ import print_function
import sys
import os
import logging
import re
import gzip
from access import db
from datetime import datetime
from glob import glob
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '1.8.0'

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

def get_seq_type_dir(sample):

    seq_type_dir = 'exomes'

    try:
        application_tag = sample.udf["Sequencing Analysis"]
    except KeyError:
        application_tag = None

    logging.info('Application tag: {}'.format(application_tag))
    if application_tag is None:
        logging.warning("Application tag not defined for {}".format(sample_id))
        seq_type_dir = 'exomes'
    else:
      if len(application_tag) != 10:
          logging.error("Application tag '{}' is wrong for {}".format(applitcation_tag, sample_id))
          return None

      seq_type = application_tag[0:3]
      if seq_type == 'EXX':
          seq_type_dir = 'exomes'
      elif seq_type == 'WGx':
          seq_type_dir = 'genomes'
      else:
          logging.error("'{}': unrecognized sequencing type '{}'".format(sample_id, seq_type))
          return None

    if application_tag == 'RML': # skip Ready Made Libraries
        logging.warning("Ready Made Library. Skipping link creation for {}".format(sample_id))
        return None

    return seq_type_dir

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
        logging.error("'{}' internal customer name is not set".format(sample_id))
        return None

    if not re.match(r'cust\d{3}', cust_name):
        logging.error("'{}' does not match an internal customer name".format(cust_name))
        return None

    return cust_name

def get_index(fastq_file_name):
    with gzip.open(fastq_file_name, 'rb') as f:
        line = f.readline().rstrip() 
        while not line.startswith('@'):
            line = f.readline().rstrip()
        
        index = line.split(':')[9]
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

def main(argv):

    logger.info('Version: {} {}'.format(__file__, __version__))
    
    indir = '/mnt/hds/proj/bioinfo/EXTERNAL/'
    outdir = '/mnt/hds/proj/bioinfo/MIP_ANALYSIS/'
  
    if len(argv) > 0:
        try:
            argv[0]
        except NameError:
            sys.exit("Usage: {} <full path to fastq dir>".format(__file__))
        else:
            start_dir = argv[0]
    else:
        sys.exit("Usage: {} <full path to fastq dir>".format(__file__))
  
    for fastq_full_file_name in glob(os.path.join(start_dir, '*fastq.gz')):
        fastq_file_name = os.path.basename(fastq_full_file_name)
        fastq_file_name_split = fastq_file_name.split('_')

        # get info frmo the sample file name
        lane = fastq_file_name_split[0]
        # make the external id more idiot proof by slicing off lane and direction
        sample_id = fastq_file_name_split[1:-1][0]
        direction = fastq_file_name_split[-1] # will also have the ext

        # get info from LIMS
        sample = get_sample(sample_id)
        family_id = get_family_id(sample)
        cust_name = get_cust_name(sample)
        seq_type_dir = get_seq_type_dir(sample)
        date = datetime.strptime(sample.date_received, "%Y-%m-%d").strftime("%y%m%d")

        # some more info
        index = get_index(fastq_full_file_name)
        FC = 'EXTERNALX' # ok, 9 letters long to emulate a FC name
        
        # create dest dir
        complete_outdir = os.path.join(outdir, cust_name, family_id, seq_type_dir, sample_id, 'fastq')
        logging.info(complete_outdir)
        if not os.path.isdir(complete_outdir):
            try:
                logging.info('mkdir -p ' + complete_outdir)
                os.makedirs(complete_outdir)
            except OSError:
                logging.warning('Failed to create {}'.format(complete_outdir))
                exit()

        # link!
        make_link(
            fastq_full_file_name,
            os.path.join(
                complete_outdir,
                '_'.join( [lane, date, FC, sample_id, index, direction ])
            ),
            'soft'
        )

if __name__ == '__main__':
    setup_logging('DEBUG')
    main(sys.argv[1:])
