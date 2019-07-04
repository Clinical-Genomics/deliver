"""CLI for deliver package"""

import sys
import logging
import yaml

import click

from .exc import MissingFlowcellError
from .modules.demux import is_pooled_lane, get_fastq_files, getsampleinfo
from .modules.inbox import inbox_links
from .modules.microbial import link_microbial
from .utils.fastq import get_lane, is_undetermined
from .ext import ext
from .modules.db import CgStats

LOG = logging.getLogger(__name__)

__version__ = '2.3.1'

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
@click.argument('infile', type=click.Path(exists=True))
@click.option('-s', '--sample', help='Sample ID.\
        If set, will deliver to custXXX/inbox/{family}/{sample}')
@click.option('-p', '--project', help='Project ID. If set, will deliver to custXXX/inbox/{family}')
@click.option('-c', '--case', help='case name. If set, will deliver to custXXX/inbox/{family}')
@click.option('--cust', help='Customer name')
@click.option('--outdir', help='Path to customer folders')
@click.pass_context
def inbox(context, infile, sample, project, case, cust, outdir):
    """links files to custXXX/inbox/project"""
    if not outdir:
        outdir = context.obj['inbox_root']
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
        LOG.error("can't find flowcell: %s", error.message)
        context.abort()


@link.command('ls')
@click.option('-f', '--flowcell', default=None)
@click.option('-l', '--lane', default=None)
@click.option('-s', '--sample', default=None)
@click.option('-c', '--check', is_flag=True, default=True, help='Check expected fastq files')
@click.option('-F', '--force', is_flag=True, default=False, help='Include undetermined')
@click.pass_context
def list_(context, flowcell, lane, sample, check, force):
    """List the fastq files."""

    fastq_files = []
    demux_root = context.obj['demux_root']
    host = context.obj['cgstats']['host']
    port = context.obj['cgstats']['port']
    db   = context.obj['cgstats']['db']
    user = context.obj['cgstats']['user']
    password = context.obj['cgstats']['password']

    with CgStats().connect(host, port, db, user, password) as cursor:
        if check:
            sample_infos = getsampleinfo(cursor, flowcell, lane, sample)
            for sample_info in sample_infos:
                flowcell = sample_info['flowcell']
                lane = sample_info['lane']
                samplename = sample_info['samplename']
                fastq_files.extend(get_fastq_files(demux_root, flowcell, lane, samplename))
        else:
            flowcell = flowcell if flowcell else '*'
            lane = lane if lane else '?'
            sample = sample if sample else '*'
            fastq_files = get_fastq_files(demux_root, flowcell, lane, sample)

        if not fastq_files:
            context.abort()

        for fastq_file in fastq_files:
            link_me = force or not \
                      (is_pooled_lane(cursor, flowcell, get_lane(fastq_file)) and is_undetermined(fastq_file))
            if link_me:
                click.echo(fastq_file)


def setup_logging(level='INFO'):
    """Set the default log output"""
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
