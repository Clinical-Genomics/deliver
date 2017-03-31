#!/usr/bin/python

from __future__ import print_function
import logging
import re
import gzip
import time

from path import Path
from datetime import datetime
from glob import glob

from cglims.api import ClinicalLims, ClinicalSample
from ..utils.files import make_link

__version__ = '1.9.0'

logger = logging.getLogger(__name__)


def get_index(fastq_file_name):
    with gzip.open(fastq_file_name, 'rb') as f:
        line = f.readline().rstrip()
        while not line.startswith('@'):
            line = f.readline().rstrip()

        index = line.split(':')[-1]

        # possible early fastq header line
        if '#' in index:
            # @HWUSI-EAS100R:6:73:941:1973#0/1
            m = re.search(r'.*#(.+)/.*', index)
            if m:
                index = m.group(1)

        return index


def ext_links(config, start_dir, outdir):

    lims_api = ClinicalLims(**config['lims'])
    # make sure we don't link with the relative path
    outdir = Path(outdir).abspath()

    for fastq_full_file_name in glob(Path(start_dir).joinpath('*fastq.gz')):
        fastq_file_name = Path(fastq_full_file_name).basename()
        fastq_file_name_split = fastq_file_name.split('_')

        # get info from the sample file name
        lane = fastq_file_name_split[0]
        # will also have the ext
        direction = fastq_file_name_split[-1]
        sample_id = fastq_file_name_split[3]
        index = fastq_file_name_split[4]
        FC = fastq_file_name_split[2]
        if FC == '0':
            FC = 'EXTERNALX'

        # get info from LIMS
        sample = lims_api.sample(sample_id)
        cgsample = ClinicalSample(sample)
        family_id = sample.udf.get('familyID', None)
        cust_name = sample.udf['customer']
        # get wes|wgs
        seq_type_dir = cgsample.apptag.analysis_type
        if sample.date_received is not None:
            date = datetime.strptime(sample.date_received, "%Y-%m-%d").strftime("%y%m%d")
        else:
            mtime = Path(fastq_full_file_name).getmtime()
            date = time.strftime("%y%m%d", time.localtime(mtime))

        # some more info
        if index == '0':
            index = get_index(fastq_full_file_name)

        # create dest dir
        complete_outdir = Path(outdir).joinpath(cust_name, family_id, seq_type_dir, sample_id, 'fastq')
        out_filename = '_'.join([lane, date, FC, sample_id, index, direction])
        dest = Path(complete_outdir).joinpath(out_filename)

        # check if file already exists
        if Path(dest).isfile():
            logger.debug('Skipping creation of {}. Already exists'.format(dest))
            continue

        # create the out dir
        logger.debug('mkdir -p ' + complete_outdir)
        Path(complete_outdir).makedirs_p()

        # link!
        success = make_link(fastq_full_file_name, dest, 'soft')

        if success:
            logger.info("ln -s {} {} ...".format(fastq_full_file_name, dest))
        else:
            logger.error("{} -> {}".format(fastq_full_file_name, dest))
