#!/usr/bin/python
"""
Deliver files from Housekeeper to the customer's inbox.

=> INPUT: cust name, sample name, housekeeper file (bam, vcf, bcf, ...)

=> CONFIG: root_dir, clinstatsdb_connection
"""

from __future__ import print_function
import sys
import logging
import yaml
import grp

from glob import glob
from path import path

from cglims.api import ClinicalLims, ClinicalSample

from ..utils import get_mipname, make_link


logger = logging.getLogger(__name__)


def inbox_links(config, infile, sample_id, outdir, cust=None):

    lims_api = ClinicalLims(**config['lims'])
    outdir = outdir + '/{cust}/INBOX/{group}/{sample}'
    infile_name = path(infile).basename()
    sample = lims_api.sample(sample_id)

    cg_sample = ClinicalSample(sample)
    cust_sample_id = sample.name
    if cg_sample.pipeline == 'mwgs':
        group = sample.project.id
    else:
        group = sample.udf['familyID']

    if not cust:
        cust = sample.udf['customer']

    complete_outdir = path.joinpath(outdir.format(
        cust=cust, group=group, sample=cust_sample_id
    ))

    if infile_name.endswith('fastq.gz'):
        # the sample name is in the path, not the file name
        fastq_mipname = get_mipname(infile)
        cust_file_name = rename_file(fastq_mipname, sample_id, cust_sample_id)
    else:
        cust_file_name = rename_file(str(infile_name), sample_id, cust_sample_id)
    path(complete_outdir).makedirs_p()

    outfile = path.joinpath(complete_outdir, cust_file_name)

    # link!
    link_rs = make_link(
        infile,
        outfile,
        link_type='hard'
    )

    if link_rs:
        logger.info("Linked {}".format(outfile))


def rename_file(file_name, sample_id, cust_sample_id):
    return file_name.replace(sample_id, cust_sample_id)
