#!/usr/bin/python

from __future__ import print_function
import os
import sys
import logging
import grp
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD
from pymip.api import sampleinfo

logger = logging.getLogger(__name__)

def _get_sample(lims, sample_name):
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
            return False

    return sample

def get_cust_sample_name(lims, sample_name):

    sample = _get_sample(lims, sample_name)

    if not sample:
        return sample_name

    try:
        cust_sample_name = sample.name
    except AttributeError:
        logger.warn("'{}' does not have a customer sample name!".format(sample_name))
        return sample_name

    return cust_sample_name

def get_family_id(lims, sample_name):
    """TODO: Docstring for get_family_id.
    Returns (str): the family ID

    """
    sample = _get_sample(lims, sample_name)

    if not sample:
        return False

    try:
        family_id = sample.udf['familyID']
    except KeyError as e:
        logger.error("Family ID name not set for '{}'".format(sample_name))
        return False

    return family_id

def get_sequencing_type(lims, sample_name):
    """Gets the sequencing type based on the application tag: exome or genome
    Returns (str): genome or exome

    """
    sample = _get_sample(lims, sample_name)

    if not sample:
        return False

    application_tag = sample.udf['Sequencing Analysis']
    sequencing_type = 'exomes'

    if application_tag is None:
        logger.error('Application tag is not set')
        return False

    else:
        if len(application_tag) != 10:
            logger.error("Faulty application tag '{}'".format(application_tag))
            return False

        seq_type = application_tag[0:3]
        if seq_type == 'EXO':
            sequencing_type = 'exomes'
        elif seq_type == 'EXX':
            sequencing_type = 'exomes'
        elif seq_type == 'WGS':
            sequencing_type = 'genomes'
        elif seq_type == 'WGX':
            sequencing_type = 'genomes'
        elif seq_type == 'RML': # skip Ready Made Libraries
            sequencing_type = 'exomes'
        else:
            logger.error("Unrecognized sequencing type '{}' for '{}'".format(seq_type, sample_name))
            return False

    return sequencing_type

def get_cust_name(lims, sample_name):
    """ Queries the LIMS for the customer name of the sample
    Returns (str): customer name

    """
    # TODO validate the name of the cust!
    sample = _get_sample(lims, sample_name)

    if not sample:
        return False

    try:
        customer = sample.udf['customer']
    except KeyError as e:
        logger.error("Customer name not set for '{}'".format(sample_name))
        return False

    return customer

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

def vcf_links(qc_sample_info_file, outdir):

    outdir = outdir + '/{cust}/INBOX/{seq_type}/{cust_sample_name}/'

    params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    # parse the yaml file
    with open(qc_sample_info_file, 'r') as stream:
        qc_sample_info = sampleinfo.BaseSampleInfo()
        qc_sample_info.load_sampleinfo(stream)
        bcf_file_path = qc_sample_info.bcf_path
        bcf_file = os.path.basename(bcf_file_path)
        bcf_start_dir = os.path.dirname(bcf_file_path)

    for sample_name in qc_sample_info._samples.keys():
        seq_type = get_sequencing_type(lims, sample_name)

        cust = get_cust_name(lims, sample_name)

        # get the customer external sample name
        cust_sample_name = get_cust_sample_name(lims, sample_name)

        # get the family id
        cust_family_id = get_family_id(lims, sample_name)

        # rename the vcf file
        bcf_cust_file = rename_file(bcf_file, cust_family_id, cust_sample_name)
        #import ipdb; ipdb.set_trace()

        # create cust folder
        logging.info('creating cust folder')
        try:
            os.makedirs(os.path.join(outdir.format(cust=cust, seq_type=seq_type, cust_sample_name=cust_sample_name)))
        except OSError:
            pass

        # link!
        logging.info('linking')
        make_link(
            os.path.join(bcf_start_dir, bcf_file),
            os.path.join(outdir.format(cust=cust, seq_type=seq_type, cust_sample_name=cust_sample_name), bcf_cust_file)
        )

if __name__ == '__main__':
    setup_logging(level='DEBUG')
    main(sys.argv[1:])
