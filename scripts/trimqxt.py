#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import glob
import logging
import os
import subprocess
import tempfile
import datetime
import shutil
from access import db, lims

__version__ = '1.30.9'

logger = logging.getLogger(__name__)


def get_sample_names(rundir):
    """Get all sample names from a RUN directory.

    All sample names have been cleaned:
    * library prep has been removed
    * B (reprep), F (fail) suffixes have been removed

    Args:
      rundir (str): FQ path to the run

    Returns:
        list: a list of sample names
    """
    return get_sample_paths(rundir).keys()


def get_sample_paths(rundir):
    """Associate samples with their path.

    All sample names have been cleaned:
    * library prep has been removed
    * B (reprep), F (fail) suffixes have been removed

    Args:
      rundir (str): FQ path to the run

    Returns:
    dict: ``{sample: path}``
    """
    sample_paths = glob.glob("{}/Unalign*/Project_*/Sample_*".format(rundir))
    samples = {}
    for sample_path in sample_paths:
        sample_id = os.path.basename(sample_path).split('_')[1]
        # remove the reprep (B) and reception control fail (F) indicators
        # from the sample name
        clean_sample_id = sample_id.rstrip('BF')
        samples[clean_sample_id] = sample_path

    return samples


def launch_trim(trim_indir, trim_outdir, link_dir):
    """Creates sbatch scripts and launches them.
    Last sbatch script will create the 'trimmed.txt' file denoting a succesful run.

    Args:
        trim_indir (str): path to fastq files in need of trimming
        trim_outdir (str): path to output directory
        link_dir (str): path to where trimmed fastq files should be linked to

    Returns:
        list: launched sbatch ids
    """
    script_dir = os.path.join(trim_indir, 'scripts')
    try:
        os.makedirs(script_dir)
    except OSError:
        pass

    sbatch_ids = []
    read1_fastq_paths = glob.glob('{}/*_R1_*.fastq.gz'.format(trim_indir))
    for read1_path in read1_fastq_paths:
        read2_path = read1_path.replace('_R1_', '_R2_')
        read1_file = os.path.basename(read1_path)
        read2_file = os.path.basename(read2_path)
        outfile = os.path.join(trim_outdir, read1_file.replace('.fastq.gz', '')) 
        read1_out = os.path.join(trim_outdir, read1_file.replace('.fastq.gz', '.trimmed.fastq.gz'))
        read2_out = os.path.join(trim_outdir, read2_file.replace('.fastq.gz', '.trimmed.fastq.gz'))

        with tempfile.NamedTemporaryFile(dir=script_dir, delete=False) as sbatch_file:
            file_content = """#!/bin/bash
            set -e

            java -jar /mnt/hds/proj/bioinfo/SCRIPTS/AgilentReadTrimmer.jar -m1 {read1} -m2 {read2} -o {outfile} -qxt && gzip {outfile}*

            mv {outfile}_1.fastq.gz {read1_out}
            mv {outfile}_2.fastq.gz {read2_out}

            ln -s {read1_out} {link_dir}/
            ln -s {read2_out} {link_dir}/
            """.format(read1=read1_path, read2=read2_path, outfile=outfile,
                       read1_out=read1_out, read2_out=read2_out, link_dir=link_dir)

            sbatch_file.write(file_content)
            sbatch_file.flush()

            try:
                out_path = "/mnt/hds/proj/bioinfo/LOG/fastqTrimming.%j.out"
                err_path = "/mnt/hds/proj/bioinfo/LOG/fastqTrimming.%j.err"
                command = ("sbatch -A prod001 -t 12:00:00 -J fastqTrimming -c 1 -o"
                           "{out} -e {error}".format(out=out_path, error=err_path))

                command_line = command.split(' ')
                command_line.append(sbatch_file.name)
                logger.debug(' '.join(command_line))
                sbatch_output = subprocess.check_output(command_line)
                sbatch_ids.append(sbatch_output.rstrip().split(' ')[-1])

            except subprocess.CalledProcessError as exception:
                message = "The command {} failed".format(' '.join(command_line))
                exception.message = message
                raise exception

    return sbatch_ids


def launch_end(trim_indir, base_dir, sbatch_ids):
    script_dir = os.path.join(trim_indir, 'scripts')

    # once all the jobs succesfully finish, symlink the files back
    with tempfile.NamedTemporaryFile(delete=False, dir=script_dir) as finished_file:
        content = """#!/bin/bash
        date +"%Y%m%d%H%M%S" > {base}/trimmed.txt
        rm {base}/trimming.txt
        """.format(base=base_dir)
        finished_file.write(content)
        finished_file.flush()

    try:
        output = '/mnt/hds/proj/bioinfo/LOG/trimmingFinished.%j.out'
        error = '/mnt/hds/proj/bioinfo/LOG/trimmingFinished.%j.err'
        dependencies = ':'.join(sbatch_ids)
        command = ("sbatch -A prod001 -t 00:01:00 -J trimmingFinished -c 1 "
                   "-o {out} -e {error} --dependency=afterok:{deps}"
                   .format(out=output, error=error, deps=dependencies))

        command_line = command.split(' ')
        command_line.append(finished_file.name)
        logger.debug(' '.join(command_line))
        subprocess.check_output(command_line)

    except subprocess.CalledProcessError as exception:
        exception.message = "The command {} failed.".format(' '.join(command_line))
        raise exception


def main(argv):
    """Takes one param: the run dir"""
    logger.info(__version__)
    rundir = argv[0]

    # get all samples of this run
    samples = get_sample_paths(rundir)
    logger.info("Found %s samples: %s", len(samples), samples)
    # determine which samples are QXT
    params = db.readconfig('non')
    
    sbatch_ids = []
    for sample, sample_path in samples.items():
        with lims.limsconnect(params['apiuser'], params['apipass'],
                              params['baseuri']) as lmc:

            application_tag = lmc.getattribute('samples', sample, 'Sequencing Analysis')
            if application_tag is None:
                logger.warning("Application tag not defined for %s", sample)
                # skip to the next sample
                continue

            logger.info("Application Tag: %s -> %s", sample, application_tag)

            kit_type = application_tag[3:6]
            if kit_type == 'QXT':
                logger.info("Sample %s is QXT! Trimming ...", sample)
                # TODO: check clinstatsdb if sample is trimmed already
                # move the samples to a totrim dir so they don't get picked up by next steps ...
                sample_base_path = os.path.dirname(sample_path)
                trim_dir = os.path.join(sample_base_path, 'totrim')
                outdir = os.path.join(sample_base_path, 'trimmed')

                fastq_dir = os.path.basename(sample_path)
                fastq_trim_dir = os.path.join(trim_dir, fastq_dir)
                fastq_outdir = os.path.join(outdir, fastq_dir)

                # skip this sample if the input dir exists
                if os.path.exists(fastq_trim_dir):
                    logger.info("%s exists, skipping!", fastq_trim_dir)
                    continue

                # skip the sample if output dir not empty
                if os.path.exists(fastq_outdir):
                    for _, _, files in os.walk(fastq_outdir):
                        if files:
                            logger.info("%s not empty, skipping!", fastq_outdir)
                            continue

                # create input dir
                try:
                    # only create trim_dir, the fastq_dir will me moved in here
                    logger.debug("mkdir %s", trim_dir)
                    os.makedirs(trim_dir)
                except OSError:
                    pass

                # create the output dir
                try:
                    logger.debug("mkdir %s", fastq_outdir)
                    os.makedirs(fastq_outdir)
                except OSError:
                    pass

                # move the fastq files to the totrim dir
                logger.debug("mv %s %s", sample_path, fastq_trim_dir)
                shutil.move(sample_path, fastq_trim_dir)

                # create the original sample dirtory
                try:
                    logger.debug("mkdir %s", sample_path)
                    os.makedirs(sample_path)
                except OSError:
                    pass

                # indicate that we are trimming, let other steps in the data flow
                # wait will be removed on succesful finishing trimming
                with open("{}/trimming.txt".format(rundir), 'w') as t_file:
                    t_file.write(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

                # lauch trim!
                new_sbatch_ids = launch_trim(trim_indir=fastq_trim_dir,
                                             trim_outdir=fastq_outdir,
                                             link_dir=sample_path)
                sbatch_ids.extend(new_sbatch_ids)

    # if we have launched jobs, wait for them before creating a simple
    # trimmed.txt file
    if sbatch_ids:
        launch_end(trim_indir=fastq_trim_dir, base_dir=rundir, sbatch_ids=sbatch_ids)

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


if __name__ == '__main__':
    setup_logging(level='DEBUG')
    main(sys.argv[1:])
