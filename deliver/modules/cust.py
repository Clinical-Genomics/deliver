#!/usr/bin/python

from __future__ import print_function
import sys
import logging
import logging.handlers
import re

from StringIO import StringIO
from path import path

from cglims.api import ClinicalLims, ClinicalSample
from ..utils.files import make_link

__version__ = '1.20.22'

logger = logging.getLogger(__name__)

class ExternalIDNotFoundException(Exception):
    pass

class MalformedCustomerIDException(Exception):
    def __init__(self, customer, sample_id):
        self.customer = customer
        self.sample_id = sample_id

    def __str__(self):
        return repr("Customer name '{}' for '{}' is not correctly formatted in LIMS".format(self.customer, self.sample_id))

def get_sample(lims_api, external_id):
    """ Looks up a sample based on an external ID in LIMS

    args:
        external_id (str): external sample ID

    Returns: ClinicalSample, None
    """

    try:
        samples = lims_api.get_samples(name=external_id)
    except:
        logger.error("External ID '{}' was not found in LIMS".format(external_id))
        raise ExternalIDNotFoundException("External ID '{}' was not found in LIMS".format(external_id))

    # multiple samples could be returned
    # take those that are marked as externally sequenced
    ext_samples = []
    for sample in samples:
        cgsample = ClinicalSample(sample)
        apptag = cgsample.apptag

        if apptag.is_external:
            ext_samples.append(sample)

    ext_samples.sort(key=lambda x: x.date_received, reverse=True)

    if len(samples) and len(ext_samples) == 0:
        logger.error("External ID '{}' does not have correct application tag {}".format(external_id, apptag))
        raise ExternalIDNotFoundException("External ID '{}' does not have correct application tag {}".format(external_id, apptag))

    return ext_samples.pop()


def get_parts(filename):
    """ Determines the FC, lane, external_id, index, date, extension, and direction from a filename.

    Args:
        filename (str): the filename to examine.

    Returns (dict)
    """

    # standard values
    lane  = '1'
    date  = '0'
    FC    = '0'
    index = '0'
    # direction
    # external_id

    filename_split = filename.split('_')
    direction, extension = filename_split[-1].split('.', 1)
    direction = str(int(direction)) # easy way of removing leading zero's

    # four formats: external-id_direction, lane_external-id_direction, LANE_DATE_FC_SAMPLE_INDEX_DIRECTION, SAMPLE_FC_LANE_DIRECTION_PART
    if len(filename_split) == 2:
        logger.info('Found SAMPLE_DIRECTION format: {}'.format(filename))

        external_id = filename_split[:-1]
    elif len(filename_split) == 3:
        logger.info('Found LANE_SAMPLE_DIRECTION format: {}'.format(filename))

        lane  = filename_split[0]
        external_id = filename_split[1:-1]
    elif len(filename_split) == 6:
        logger.info('Found LANE_DATE_FC_SAMPLE_INDEX_DIRECTION format: {}'.format(filename))

        date  = filename_split[1]
        FC    = filename_split[2]
        index = filename_split[4]
        lane  = filename_split[0]
        external_id = filename_split[3]
    elif len(filename_split) == 5:
        m = re.match(r'(.*?)_(.*?)_L(\d+)_R(\d+)_(\d+)', filename)
        if m:
            logger.info('Found SAMPLE_INDEX_LANE_DIRECTION_PART format: {}'.format(filename))

            if not re.match(r'S\d', m.group(2)):
                index = m.group(2)
            lane  = str(int(m.group(3)))
            external_id = m.group(1)
            direction = m.group(4)

    return {
        'lane': lane,
        'date': date,
        'FC': FC,
        'index': index,
        'external_id': external_id,
        'direction': direction,
        'extension': extension
    }


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

def cust_links(config, fastq_full_file_name, outdir):
    """ Based on an input file name:
        * determine what format the file name has
        * pick out sample name, read direction, lane, flowcell, date, index
        * link the input file to the outdir renamed to fit MIP naming scheme.

    Args:
        fastq_full_file_name (str): full path to the input file
        outdir (str): the path to the outdir

    """
    lims_api = ClinicalLims(**config['lims'])
    outdir = path(outdir).abspath() # make sure we don't link with the relative path

    fastq_file_name = path(fastq_full_file_name).basename() # get the file name
    fastq_target_file = path(fastq_full_file_name).realpath() # resolve symlinks

    # set up logging
    log_file = path(outdir).joinpath(fastq_file_name + '.log')
    log_level = config.get('log_level', 'INFO')
    setup_logging(level=log_level, delayed_logging=True) # make sure we set up a logger buffer we can write to file later

    parts = get_parts(fastq_file_name)

    sample = get_sample(lims_api, parts['external_id'])
    internal_id = sample.id
    customer = sample.udf['customer']

    out_file_name = '_'.join([
        parts['lane'], parts['date'], parts['FC'], internal_id, parts['index'], parts['direction']
    ])
    out_file_name = '{}.{}'.format(out_file_name, parts['extension'])

    # make out dir
    complete_outdir = path(outdir).joinpath(customer, internal_id)
    path(complete_outdir).mkdir_p()

    # link!
    dest = path(complete_outdir).joinpath(out_file_name)
    path(dest).remove_p()
    success = make_link(
        fastq_target_file,
        dest,
        'hard'
    )

    if success:
        logger.info("ln {} {} ...".format(fastq_target_file, dest))
    else:
        logger.error("{} -> {}".format(fastq_target_file, dest))

    # append the log to the project log
    setup_logfile(path(complete_outdir).joinpath('project.log'))
