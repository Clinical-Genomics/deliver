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


def inbox_links(config, infile, sample_lims_id, outdir, cust=None):

    lims_api = ClinicalLims(**config['lims'])
    outdir = outdir + '/{cust}/INBOX/{family_id}/'
    infile_name = path(infile).basename()
    lims_sample = lims_api.sample(sample_lims_id)
    cust_sample_name = lims_sample.name
    family_id = lims_sample.udf['familyID']
    if not cust:
        cust = lims_sample.udf['customer']
    complete_outdir = path.joinpath(outdir.format(
        cust=cust, family_id=family_id
    ))

    cust_file_name = rename_file(str(infile_name), sample_lims_id, cust_sample_name)
    path(complete_outdir).makedirs_p()

    # link!
    make_link(
        infile,
        path.joinpath(complete_outdir, cust_file_name)
    )


def rename_file(file_name, sample_name, cust_sample_name):
    return file_name.replace(sample_name, cust_sample_name)


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
    except:
        logging.error("Can't create symlink from {} to {}".format(source, dest))
