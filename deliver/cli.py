"""CLI for deliver package"""

import logging
import yaml

import click

from .exc import MissingFlowcellError
from .modules.inbox import inbox_links
from .modules.microbial import link_microbial
from .ext import ext

LOG = logging.getLogger(__name__)

__version__ = '1.36.0'

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
@click.option('--outdir', show_default=True, help='Path to customer folders')
@click.pass_context
def inbox(context, infile, sample, project, case, cust, outdir):
    """links files to custXXX/inbox/project"""
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
