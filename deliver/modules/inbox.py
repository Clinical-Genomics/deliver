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


def inbox_links(config, infile, outdir, sample_id=None, project=None, cust=None):

    lims_api = ClinicalLims(**config['lims'])
    infile_name = path(infile).basename()

    outdir_parts = {
        'outdir': outdir,
        'cust': None,
        'INBOX': 'INBOX',
        'group': None
    }

    if project:
        outdir_template = '{outdir}/{cust}/INBOX/{group}/'
        samples = lims_api.get_samples(projectlimsid=project)
        sample = samples[0]
        sample_id = sample.id
    else:
        outdir_template = '{outdir}/{cust}/INBOX/{group}/{sample}'
        sample = lims_api.sample(sample_id)
        outdir_parts['sample'] = sample.name

    cg_sample = ClinicalSample(sample)

    if not cust:
        cust = sample.udf['customer']
    outdir_parts['cust'] = cust

    if cg_sample.pipeline == 'mwgs':
        group = sample.project.id
    else:
        group = sample.udf['familyID']
    outdir_parts['group'] = group

    complete_outdir = outdir_template.format(**outdir_parts)
    cust_sample_id = sample.name

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
    path(outfile).chmod(0o644)
    #gid = grp.getgrnam("users").gr_gid
    #path(dest).chown(-1, gid) # seems to throw an OSError

    if link_rs:
        logger.info("Linked {}".format(outfile))


def rename_file(file_name, sample_id, cust_sample_id):
    return file_name.replace(sample_id, cust_sample_id)
