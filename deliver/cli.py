# -*- coding: utf-8 -*-
import logging
import click
import yaml

from .exc import MissingFlowcellError
from .modules.demux import demux_links
from .modules.ext import ext_links
from .modules.bam import bam_links
from .modules.vcf import vcf_links
from .modules.cust import cust_links
from .modules.microbial import link_microbial

log = logging.getLogger(__name__)

__version__ = '1.20.16'


@click.group()
@click.option('-l', '--log-level', default='INFO')
@click.option('-c', '--config', type=click.File('r'))
@click.pass_context
def link(context, log_level, config):
    """Make linking of FASTQ/BAM files easier!"""
    setup_logging(level=log_level)
    context.obj = yaml.load(config) if config else {}


@link.command()
@click.argument('flowcell', nargs=1)
@click.option('--custoutdir', default='/mnt/hds/proj/', show_default=True, type=click.Path(exists=True), help='path to customer folders')
@click.option('--mipoutdir', default='/mnt/hds/proj/bioinfo/MIP_ANALYSIS/', show_default=True, type=click.Path(exists=True), help='path to MIP_ANALYSIS')
@click.option('--skip-stats', is_flag=True, help='Link to cust INBOX without having stats. BEWARE that Undetermined indexes will be linked as well even if pooled sample!')
@click.option('--skip-undetermined', is_flag=True, help='Skip linking undetermined.')
@click.help_option()
def demux(flowcell, custoutdir, mipoutdir, skip_stats, skip_undetermined):
    """Links from DEMUX to MIP_ANALYSIS and customer folder"""
    demux_links(flowcell, custoutdir, mipoutdir, skip_stats)


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


@link.command()
@click.option('-r', '--root-dir', type=click.Path(exists=True))
@click.option('-s', '--sample', help='link a specific sample')
@click.option('-f', '--flowcell', help='link all samples on a flowcell')
@click.option('-d', '--dry-run', is_flag=True)
@click.argument('project', required=False)
@click.pass_context
def microbial(context, root_dir, sample, flowcell, dry_run, project):
    """Link FASTQ files to microbial substructure."""
    if root_dir:
        context.obj['microbial_root'] = root_dir
    try:
        link_microbial(context.obj, flowcell=flowcell, project=project,
                       sample=sample, dry_run=dry_run)
    except MissingFlowcellError as error:
        log.error("can't find flowcell: %s", error.message)
        context.abort()


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
    log.info('Version: {} {}'.format(__file__, __version__))
    link()
