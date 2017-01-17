# -*- coding: utf-8 -*-
import logging
import click

from .modules.ext import ext_links
from .modules.cust import cust_links


log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def ext(context):
    """ Linking files from externally sequenced samples """
    pass


@ext.command()
@click.argument('sample_folder', nargs=1, type=click.Path(exists=True))
@click.option('--outdir', default='/mnt/hds/proj/bioinfo/MIP_ANALYSIS/', show_default=True, type=click.Path(exists=True), help='path to MIP_ANALYSIS')
def mip(context, sample_folder, outdir):
    """links from EXTERNAL to MIP_ANALYSIS"""
    ext_links(sample_folder, outdir)


@ext.command()
@click.argument('fastq_file', nargs=1, type=click.Path(exists=True))
@click.option('--outdir', default='/mnt/hds/proj/bioinfo/EXTERNAL/', show_default=True, help='path to EXTERNAL folder')
def inbox(context, fastq_file, outdir):
    """links FASTQ file to EXTERNAL"""
    cust_links(fastq_file, outdir)


ext.add_command(mip)
ext.add_command(inbox)
