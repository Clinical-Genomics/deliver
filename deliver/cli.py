# -*- coding: utf-8 -*-
import logging
import click
import yaml

from .exc import MissingFlowcellError
from .modules.demux import demux_links, is_pooled_lane, get_fastq_files, getsampleinfo
from .modules.inbox import inbox_links
from .modules.microbial import link_microbial
from .utils.fastq import get_lane, is_undetermined
from .ext import ext

log = logging.getLogger(__name__)

__version__ = '1.30.1'
DEMUXDIR='/mnt/hds/proj/bioinfo/DEMUX/'


@click.group()
@click.option('-l', '--log-level', default='INFO', envvar='LOGLEVEL')
@click.option('-c', '--config', type=click.File('r'))
@click.version_option(version=__version__, prog_name="deliver")
@click.pass_context
def link(context, log_level, config):
    """Make linking of FASTQ/BAM files easier!"""
    setup_logging(level=log_level)
    context.obj = yaml.load(config) if config else {}
    context.obj['log_level'] = log_level


@link.command()
@click.option('-f', '--flowcell', help='flowcell to link')
@click.option('-s', '--sample', help='sample to link')
@click.option('-p', '--project', help='project to link [NOT IMPLEMENTED]')
@click.option('--outdir', default='/mnt/hds/proj/bioinfo/MIP_ANALYSIS/customers/', show_default=True, type=click.Path(exists=True), help='path to MIP_ANALYSIS')
@click.option('--demuxdir', default=DEMUXDIR, show_default=True, type=click.Path(exists=True), help='path to DEMUX')
@click.option('--force', is_flag=True, help='Link regardless of QC. BEWARE that Undetermined indexes will be linked as well even if pooled sample!')
@click.option('--skip-undetermined', is_flag=True, help='Skip linking undetermined.')
@click.help_option()
def mip(flowcell, sample, project, outdir, demuxdir, force, skip_undetermined):
    """Links from DEMUX to MIP_ANALYSIS and customer folder"""
    demux_links(flowcell, sample, project, outdir, demuxdir, force, skip_undetermined)


@link.command()
@click.argument('infile', type=click.Path(exists=True))
@click.option('-s', '--sample', help='Sample name. If set, will deliver to cust/INBOX/{family}/{sample}')
@click.option('-p', '--project', help='Project ID. If set, will deliver to cust/INBOX/{family}')
@click.option('-c', '--case', help='case name. If set, will deliver to cust/INBOX/{family}')
@click.option('--cust', help='Customer name')
@click.option('--outdir', default='/mnt/hds/proj/', show_default=True, help='Path to customer folders')
@click.pass_context
def inbox(context, infile, sample, project, case, cust, outdir):
    """links files to cust/INBOX/project"""
    inbox_links(context.obj, infile, outdir, sample, project, case, cust)


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


@link.command()
@click.argument('flowcell', required=True)
@click.argument('lane', required=True)
def pooled(flowcell, lane):
    """Return whether or not this lane is pooled."""

    import sys
    if is_pooled_lane(flowcell, lane):
        sys.exit(0)
    else:
        sys.exit(1)


@link.command()
@click.option('-f', '--flowcell', default=None)
@click.option('-l', '--lane', default=None)
@click.option('-s', '--sample', default=None)
@click.option('-c', '--check', is_flag=True, default=True, help='Check expected fastq files with cgstats')
@click.option('-F', '--force', is_flag=True, default=False, help='List all fastq files, including undetermined')
@click.pass_context
def ls(context, flowcell, lane, sample, check, force):
    """List the fastq files."""

    fastq_files = []
    if check:
        samples = getsampleinfo(flowcell, lane, sample)
        for rs in samples:
            flowcell = rs['flowcell']
            lane = rs['lane']
            sample = rs['samplename']
            fastq_files.extend(get_fastq_files(DEMUXDIR, flowcell, lane, sample))
    else:
        flowcell = flowcell if flowcell else '*'
        lane = lane if lane else '?'
        sample = sample if sample else '*'
        fastq_files = get_fastq_files(DEMUXDIR, flowcell, lane, sample)


    for fastq_file in fastq_files:
        link_me = force or not (is_pooled_lane(flowcell, get_lane(fastq_file)) and is_undetermined(fastq_file))
        if link_me:
            click.echo(fastq_file)


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
