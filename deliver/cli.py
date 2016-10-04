# -*- coding: utf-8 -*-
import logging
import click
from .modules.demux import demux_links
from .modules.ext   import ext_links
from .modules.bam   import bam_links
from .modules.vcf   import vcf_links
from .modules.cust  import cust_links

logger = logging.getLogger(__name__)

__version__ = '1.20.3'

@click.group()
def link():
    """Make linking of FASTQ/BAM files easier!"""
    pass

@link.command()
@click.argument('flowcell', nargs=1)
@click.option('--custoutdir', default='/mnt/hds/proj/', show_default=True, type=click.Path(exists=True), help='path to customer folders')
@click.option('--mipoutdir', default='/mnt/hds/proj/bioinfo/MIP_ANALYSIS/', show_default=True, type=click.Path(exists=True), help='path to MIP_ANALYSIS')
@click.help_option()
def demux(flowcell, custoutdir, mipoutdir):
    """Links from DEMUX to MIP_ANALYSIS and customer folder"""
    demux_links(flowcell, custoutdir, mipoutdir)

@link.command()
@click.argument('sample_folder', nargs=1, type=click.Path(exists=True))
@click.option('--outdir', default='/mnt/hds/proj/bioinfo/MIP_ANALYSIS/', show_default=True, type=click.Path(exists=True), help='path to MIP_ANALYSIS')
def ext(sample_folder, outdir):
    """links from EXTERNAL to MIP_ANALYSIS"""
    ext_links(sample_folder, outdir)

@link.command()
@click.argument('qc_sample_info_file', nargs=1, type=click.Path(exists=True))
@click.option('--outdir', default='/mnt/hds/proj/', show_default=True, help='path to customer folders')
def bam(qc_sample_info_file, outdir):
    """links BAM files to cust/INBOX"""
    bam_links(qc_sample_info_file, outdir)

@link.command()
@click.argument('qc_sample_info_file', nargs=1, type=click.Path(exists=True))
@click.option('--outdir', default='/mnt/hds/proj/', show_default=True, help='path to customer folders')
def vcf(qc_sample_info_file, outdir):
    """links bcf files to cust/INBOX"""
    vcf_links(qc_sample_info_file, outdir)


@link.command()
@click.argument('fastq_file', nargs=1, type=click.Path(exists=True))
@click.option('--outdir', default='/mnt/hds/proj/bioinfo/EXTERNAL/', show_default=True, help='path to EXTERNAL folder')
def cust(fastq_file, outdir):
    """links FASTQ file to EXTERNAL"""
    cust_links(fastq_file, outdir)

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

if __name__ == '__main__':
    setup_logging(level='DEBUG')
    logger.info('Version: {} {}'.format(__file__, __version__))
    link()
