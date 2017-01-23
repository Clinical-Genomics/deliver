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

from cglims.api import ClinicalLims


logger = logging.getLogger(__name__)


def inbox_links(config, infile, sample_id, outdir, cust=None):

    lims_api = ClinicalLims(**config['lims'])
    outdir = outdir + '/{cust}/INBOX/{family_id}/'
    infile_name = path(infile).basename()
    sample = lims_api.sample(sample_id)
    cust_sample_id = sample.name
    family_id = sample.udf['familyID']
    if not cust:
        cust = sample.udf['customer']
    complete_outdir = path.joinpath(outdir.format(
        cust=cust, family_id=family_id
    ))

    cust_file_name = rename_file(str(infile_name), sample_id, cust_sample_id)
    path(complete_outdir).makedirs_p()

    # link!
    make_link(
        infile,
        path.joinpath(complete_outdir, cust_file_name)
    )


def rename_file(file_name, sample_id, cust_sample_id):
    return file_name.replace(sample_id, cust_sample_id)


def make_link(source, dest, link_type='hard'):
    path(dest).remove_p()

    try:
        if link_type == 'soft':
            logging.info("ln -s {} {} ...".format(source, dest))
            path(source).symlink(dest)
        else:
            real_source = path(source).realpath()
            logging.info("ln {} {} ...".format(real_source, dest))
            path.link(real_source, dest)
            path(dest).chmod(0o644)
            gid = grp.getgrnam("users").gr_gid
            path(dest).chown(-1, gid)
    except Exception, e: # catch, print, and continue
        logging.error(repr(e))
