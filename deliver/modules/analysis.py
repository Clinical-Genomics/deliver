import logging
import datetime as dt
from pathlib import Path
from typing import List

import cglims
import cgstats

from deliver.exc import DeliverError, FastqFileMissingError

LOG = logging.getLogger(__name__)


def get_fastq(root_dir: str, flowcell: str, sample: str, lane: int, pooled: bool=False):
    """Find FASTQ file."""
    directory = Path(f"{root_dir}/*{flowcell}/Unaligned*/Project_*/Sample_{sample}")
    filename = f"{lane}*_{{1,2}}.fastq.gz"
    files = [file_ for file_ in directory.glob(filename) if
             (not pooled or ('Undetermined' not in file_))]
    files_found = len(files)
    if files_found == (2 if pooled else 4):
        return files
    elif files_found < (2 if pooled else 4):
        raise FastqFileMissingError(directory / filename)
    elif files_found > (2 if pooled else 4):
        raise DeliverError(f"too many files found: {directory / filename}")


def get_mipname(lane: int, flowcell: str, sample: str, read: int, undetermined: bool=False,
                date: dt.datetime=None, index: str=None) -> str:
    """Name a FASTQ file following MIP conventions."""
    flowcell = f"{flowcell}-undetermined" if undetermined else flowcell
    date_str = (date or dt.datetime.now()).strftime("%y%m%d")
    index = index if index else 'XXXXXX'
    return f"{lane}_{date_str}_{flowcell}_{sample}_{index}_{read}.fastq.gz"


def link_mip(root_dir: str, fastq_path: str, dest_name: str, customer: str, family: str,
             sample: str, sequencing_type: str):
    """Link a FASTQ file to the MIP directory structure."""
    dest_dir = Path(root_dir) / customer / family / sequencing_type / sample / 'fastq'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / dest_name
    LOG.info(f"linking: {fastq_path} -> {dest_path}")
    Path(fastq_path).symlink_to(dest_path)
