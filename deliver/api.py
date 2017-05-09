# -*- coding: utf-8 -*-

import sys
import logging
import click
import yaml

from .ext import ext

log = logging.getLogger(__name__)

def is_mip_linked(sample_id, demux_dir, mip_dir, follow=True):
    """Checks if all links are present for a sample in 
    Returns: TODO

    Needs demux_dir and mip_analysis dir


    """
    samples = getsampleinfo(flowcell, lane, sample)
    fastq_files = []
    for rs in samples:
        flowcell = rs['flowcell']
        lane = rs['lane']
        
        for fastq_file in get_fastq_files(DEMUXDIR, flowcell, lane, sample_id):
            # skip undeermined for pooled samples
            if 'Undetermined' in fastqfile:
                if is_pooled_lane(flowcell, lane):
                    log.info('Skipping pooled undetermined indexes!')
                    continue
                else:
                    fastq_files.append(fastq_file)

        outfile = get_mipname(fastqfile)
        outfile = Path(sample_outdir).joinpath(outfile)
