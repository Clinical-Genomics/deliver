# -*- coding: utf-8 -*-
import logging

from path import path

import data_delivery.trim
import data_delivery.delivery
import data_delivery.utils

logger = logging.getLogger(__name__)


def get_runs(demux_base):
    """List all run directories.

    Args:
        demux_base (path): path to demux base directory

    Returns:
        list: run folders
    """
    demux_path = path(demux_base)
    run_dirs = demux_path.listdir()
    return run_dirs


def check_status(run_dir):
    """Figure out the status is of the run."""
    complete = run_dir.joinpath('copycomplete.txt')
    delivery = run_dir.joinpath('delivery.txt')
    trimmed = run_dir.joinpath('trimmed.txt')
    trimming = run_dir.joinpath('trimming.txt')

    if complete.exists():
        logger.info('copy is complete')
        if delivery.exists():
            logger.info('delivery has started')
            return 'delivering'
        else:
            logger.info('delivery has not started')
            if trimmed.exists():
                logger.info('trimming already finished')
                return 'deliver'
            elif trimming.exists():
                logger.info('trimming is in progress')
                return 'trimming'
            else:
                logger.info("%s: ready for trimming", run_dir.basename())
                return 'trim'
    else:
        logger.info("%s not yet completely copied", run_dir.basename())
        return 'copying'


def crawl_runs(demux_base):
    """Loop over all runs."""
    all_runs = get_runs(demux_base)

    for run_dir in all_runs:
        logger.info("processing: %s", run_dir.basename())
        status = process_run(run_dir)


def process_run(run_dir):
    """Process a given run/flowcell."""
    logger.debug('deciding processing status of run')
    status = check_status(run_dir)

    # don't do anything for "delivering", "copying", "trimming"...
    if status == 'deliver':
        logger.info("%s: starting delivery", run_dir.basename())
        flowcell_id = data_delivery.utils.extract_flowcell(run_dir)
        data_delivery.delivery.main(flowcell_id)

    elif status == 'trim':
        # TODO: check if trimming is necessary
        logger.info("%s: starting trimming", run_dir.basename())
        data_delivery.trim.main(run_dir)

    return status
