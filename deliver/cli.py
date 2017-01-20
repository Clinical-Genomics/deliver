# -*- coding: utf-8 -*-
import logging
import click
import yaml

from .exc import MissingFlowcellError
from .modules.demux import demux_links
from .modules.inbox import inbox_links
from .modules.microbial import link_microbial
from .ext import ext

log = logging.getLogger(__name__)

__version__ = '1.21.10'


@click.group()
@click.option('-l', '--log-level', default='INFO')
@click.option('-c', '--config', type=click.File('r'))
@click.version_option(version=__version__, prog_name="deliver")
@click.pass_context
def link(context, log_level, config):
    """Make linking of FASTQ/BAM files easier!"""
    setup_logging(level=log_level)
    log.info('{}: version {}'.format(__package__, __version__))
    context.obj = yaml.load(config) if config else {}


@link.command()
@click.argument('flowcell', nargs=1)
@click.option('--custoutdir', default='/mnt/hds/proj/', show_default=True, type=click.Path(exists=True), help='path to customer folders')
@click.option('--mipoutdir', default='/mnt/hds/proj/bioinfo/MIP_ANALYSIS/customers/', show_default=True, type=click.Path(exists=True), help='path to MIP_ANALYSIS')
@click.option('--demuxdir', default='/mnt/hds/proj/bioinfo/DEMUX/', show_default=True, type=click.Path(exists=True), help='path to DEMUX')
@click.option('--force', is_flag=True, help='Link regardless of QC. BEWARE that Undetermined indexes will be linked as well even if pooled sample!')
@click.option('--skip-undetermined', is_flag=True, help='Skip linking undetermined.')
@click.help_option()
def mip(flowcell, custoutdir, mipoutdir, demuxdir, force, skip_undetermined):
    """Links from DEMUX to MIP_ANALYSIS and customer folder"""
    demux_links(flowcell, custoutdir, mipoutdir, demuxdir, force, skip_undetermined)


@link.command()
@click.argument('infile', type=click.Path(exists=True))
@click.option('-s', '--sample', required=True, help='Sample name')
@click.option('-c', '--cust', help='Customer name')
@click.option('--outdir', default='/mnt/hds/proj/', show_default=True, help='Path to customer folders')
@click.pass_context
def inbox(context, infile, sample, cust, outdir):
    """links files to cust/INBOX/project"""
    inbox_links(context.obj, infile, sample, outdir, cust)


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


link.add_command(ext)

if __name__ == '__main__':
    link()
