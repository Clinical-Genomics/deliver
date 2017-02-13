# -*- coding: utf-8 -*-
import logging

from path import Path


logger = logging.getLogger(__name__)


def get_lane(fastq_file):
    """Get the lane number based on a fastq file name.
    Fastq file name follows the HiSeq standard.

    Args:
        fastq_file (str): a fastq file.

    Returns (int): lane number.
    
    """
    nameparts = Path(fastq_file).basename().split("_")
    lane = int(nameparts[-3][-3:])

    return lane


def is_undetermined(fastq_file):
    """Determines if this is a Undetermined fastq file.
    Fastq file name follows the HiSeq standard.

    Args:
        fastq_file (str): a fastq file.

    Returns (bool): True if Undetermined fastq file.

    """
    nameparts = Path(fastq_file).basename().split("_")
    undetermined = ''
    if nameparts[1] == 'Undetermined':
        return True

    return False
