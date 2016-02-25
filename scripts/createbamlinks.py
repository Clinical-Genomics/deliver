#!/usr/bin/python

from __future__ import print_function
import os
import sys
import logging
import yaml
import grp
from glob import glob
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '1.6.1'

logger = logging.getLogger(__name__)

def get_cust_sample_name(lims, sample_name):
    try:
        sample = Sample(lims, id=sample_name)
        sample.get(force=True)
    except:
        try:
            logger.info("Sample {} not found in LIMS! Trying as CG ID...".format(sample_name))

            # maybe it's an old CG ID
            sample = lims.get_samples(udf={'Clinical Genomics ID': sample_name})[0]
            logger.info("Got it: {}".format(sample.id))
        except:
            logger.warn("Sample {} still not found in LIMS!".format(sample_name))
            return sample_name

    try:
        cust_sample_name = sample.name
    except AttributeError:
        logger.warn("'{}' does not have a customer sample name!".format(sample_name))
        return sample_name
    
    return cust_sample_name

def rename_file(file_name, sample_name, cust_sample_name):
    return file_name.replace(sample_name, cust_sample_name)

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
            os.chmod(dest, 0o644)
            gid = grp.getgrnam("users").gr_gid
            os.chown(dest, -1, gid)
    except:
        logging.error("Can't create symlink from {} to {}".format(source, dest))

def get_bam_files(qc_file_info):
    for case in qc_file_info.keys():
        for sample in qc_file:
            pass
        

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
    qc_sample_info_file = argv[0] # needs one argument, the qc_sample_info.yaml
    out_dir = '/mnt/hds/proj/{cust}/INBOX/genomes/{cust_sample_name}/'

    logger.info('Version: {} {}'.format(__file__, __version__))

    params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    # parse the yaml file
    with open(qc_sample_info_file, 'r') as stream:
        qc_sample_info = yaml.load(stream)
    
    for case in qc_sample_info.keys():
        for sample_name in qc_sample_info[case]:
            if sample_name == case: continue # case info, not sample info

            bam_file = qc_sample_info[case][sample_name]['MostCompleteBAM']['Path']
            bam_file_name = os.path.basename(bam_file)
            cust = bam_file.split('/')[-8]
            
            # get the customer external sample name
            cust_sample_name = get_cust_sample_name(lims, sample_name)

            # rename the bam file
            bam_cust_file_name = rename_file(bam_file_name, sample_name, cust_sample_name)
            #import ipdb; ipdb.set_trace()

            # create the customer folders and links regardless of the QC
            try:
                os.makedirs(os.path.join(out_dir.format(cust=cust, cust_sample_name=cust_sample_name)))
            except OSError:
                pass

            # link!
            make_link(
                bam_file,
                os.path.join(out_dir.format(cust=cust, cust_sample_name=cust_sample_name), bam_cust_file_name)
            )

if __name__ == '__main__':
    setup_logging(level='DEBUG')
    main(sys.argv[1:])
