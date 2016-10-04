#!/usr/bin/python

from __future__ import print_function
import sys
import os
import logging
import logging.handlers
import re
from StringIO import StringIO
from access import db
from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

__version__ = '1.20.0'

logger = logging.getLogger(__name__)

class ExternalIDNotFoundException(Exception):
    pass

class MalformedCustomerIDException(Exception):
    def __init__(self, customer, sample_id):
        self.customer = customer
        self.sample_id = sample_id

    def __str__(self):
        return repr("Customer name '{}' for '{}' is not correctly formatted in LIMS".format(self.customer, self.sample_id))

def _connect_lims():
    """ Connects to LIMS and returns Lims object

    Returns:
        Lims object

    """
    params = db.readconfig("/home/hiseq.clinical/.scilifelabrc")
    return Lims(BASEURI, USERNAME, PASSWORD)

def get_internal_id(external_id):
    """ Looks up the internal sample ID from an external ID in LIMS

    args:
        external_id (str): external sample ID

    Returns (str, None): internal sample ID or None
    """

    lims = _connect_lims()

    try:
        samples = lims.get_samples(name=external_id)
    except:
        logger.error("External ID '{}' was not found in LIMS".format(external_id))
        raise ExternalIDNotFoundException("External ID '{}' was not found in LIMS".format(external_id))

    # multiple samples could be returned
    # Take the one that has a **X tag
    ext_samples = []
    for sample in samples:
        try:
            application_tag = sample.udf["Sequencing Analysis"]
        except KeyError:
            continue

        if application_tag[2] == 'X':
            ext_samples.append(sample)

    ext_samples.sort(key=lambda x: x.date_received, reverse=True)

    if len(samples) and len(ext_samples) == 0:
        logger.error("External ID '{}' does not have correct application tag {}".format(external_id, application_tag))
        raise ExternalIDNotFoundException("External ID '{}' does not have correct application tag {}".format(external_id, application_tag))

    return ext_samples[0].id

def get_cust_name(internal_id):
    """ Looks up the customer name from an internal ID in LIMS

    Args:
        internal_id (str): the internal sample ID

    Returns (str, None):
        the customer name or None

    """

    lims = _connect_lims()

    try:
        sample = Sample(lims, id=internal_id)

        customer = sample.udf['customer']
        customer = customer.lower()
        if not re.match(r'cust\d{3}', customer):
            raise MalformedCustomerIDException(customer, internal_id)
        return customer
    except:
        raise MalformedCustomerIDException(customer, internal_id)

    return None

def make_link(source, dest, link_type='hard'):
    """ Create a hard or soft link

    Args:
        source (str): path to the source file
        dest (str): path to the destination file
        link_type (str, default hard): hard|soft link

    Returns: None
    """
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
            # unlink before making hardlink
            os.link(os.path.realpath(source), dest)
    except:
        logger.error("Can't create symlink from {} to {}".format(source, dest))

def setup_logging(level='INFO', delayed_logging=False):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # customize formatter, align each column
    template = "[%(asctime)s] %(name)-25s %(levelname)-8s %(message)s"
    formatter = logging.Formatter(template)

    # add a basic STDERR handler to the logger if none exists
    has_stream_handler = [ True for handler in root_logger.handlers if isinstance(handler, logging.StreamHandler) ]
    if not has_stream_handler:
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    # add a buffer handler to the logger
    # will be written to a log file once location of the log file is known.
    if delayed_logging:
        log_buffer_handler = logging.handlers.MemoryHandler(capacity = 1024 * 100)
        log_buffer_handler.setLevel(level)
        log_buffer_handler.setFormatter(formatter)
        root_logger.addHandler(log_buffer_handler)

    return root_logger

def setup_logfile(output_file):
    """Sets up the log file by replacing the MemoryHandler from the logger
    with a FileHandler.

    Args:
        output_file (str): The path to the target log file.
    Returns: None

    """
    # set formatter
    template = "[%(asctime)s] %(name)-25s %(levelname)-8s %(message)s"
    formatter = logging.Formatter(template)

    # create logfile handler
    file_handler = logging.FileHandler(output_file)
    file_handler.setFormatter(formatter)

    # get the MemoryHandler
    root_logger = logging.getLogger()
    log_buffer_handler = [ handler for handler in root_logger.handlers if isinstance(handler, logging.handlers.MemoryHandler) ]
    if not log_buffer_handler:
        logger.warning("Failed to find the MemoryHandler. '%s' will not be created.", output_file)
    else:
        log_buffer_handler = log_buffer_handler.pop()

        # connect the file handler with the memory handler
        log_buffer_handler.setTarget(file_handler)
        log_buffer_handler.flush()
        log_buffer_handler.close()

        # replace the memory handler with the file handler
        root_logger.removeHandler(log_buffer_handler)
        root_logger.addHandler(file_handler)

def cust_links(fastq_full_file_name, outdir):
    """ Based on an input file name:
        * determine what format the file name has
        * pick out sample name, read direction, lane, flowcell, date, index
        * link the input file to the outdir renamed to fit MIP naming scheme.

    Args:
        fastq_full_file_name (str): full path to the input file
        outdir (str): the path to the outdir

    """
    fastq_file_name = os.path.basename(fastq_full_file_name) # get the file name
    fastq_target_file = os.path.realpath(fastq_full_file_name) # resolve symlinks
    fastq_file_name_split = fastq_file_name.split('_')
    direction, extension = fastq_file_name_split[-1].split('.', 1)

    # set up logging
    log_file = os.path.join(outdir, fastq_file_name + '.log')
    setup_logging(delayed_logging=True) # make sure we set up a logger buffer we can write to file later
    logger.info('Version: {} {}'.format(__file__, __version__))

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
            logger.info('Found SAMPLE_INDEX_LANE_DIRECTION_PART format: {}'.format(fastq_file_name))

            if not re.match(r'S\d', m.group(2)):
                index = m.group(2)
            lane  = str(int(m.group(3)))
            external_id = m.group(1)
            direction = m.group(4)

    internal_id = get_internal_id(external_id)

    out_file_name = '_'.join([lane, date, FC, internal_id, index, direction])
    out_file_name = '{}.{}'.format(out_file_name, extension)

    customer = get_cust_name(internal_id)

    # make out dir
    complete_outdir = os.path.join(outdir, customer, internal_id)
    if not os.path.isdir(complete_outdir):
        try:
            logger.info('mkdir -p ' + complete_outdir)
            os.makedirs(complete_outdir)
        except OSError:
            logger.error('Failed to create {}'.format(complete_outdir))
            exit()

    # link!
    make_link(
        fastq_target_file,
        os.path.join(complete_outdir, out_file_name),
        'hard'
    )

    # append the log to the project log
    setup_logfile(os.path.join(complete_outdir, 'project.log'))

if __name__ == '__main__':
    setup_logging('DEBUG')
    main(sys.argv[1:])
