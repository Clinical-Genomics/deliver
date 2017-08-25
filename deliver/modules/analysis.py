import logging
from pathlib import Path
from typing import List

import cglims
import cgstats

LOG = logging.getLogger(__name__)


def get_fastq(root_dir: str, flowcell: str, sample: str, lane: int, tile: str=None, read: int=None):
    pattern = f"{root_dir}/*{flowcell}/Unaligned*/Project_*/Sample_{sample}"
    filename = "{lane}_{tile}*_{read}.fastq.gz"
    if tile:
        filename = "".format(tile=tile or 'NOTHING')
        filename.replace('_NOTHING_', '')


def link_mip(root_dir: str, fastq_path: str, dest_name: str, customer: str, family: str,
             sample: str, sequencing_type: str):
    """Link a FASTQ file to the MIP directory structure."""
    dest_dir = Path(root_dir) / customer / family / sequencing_type / sample / 'fastq'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / dest_name
    LOG.info(f"linking: {fastq_path} -> {dest_path}")
    Path(fastq_path).symlink_to(dest_path)
