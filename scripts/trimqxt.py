#!/usr/bin/env python
# encoding: utf-8

import sys
import glob
import os
import subprocess
import tempfile
from access import db, lims

def get_sample_names(rundir):
  """Gets all the names of the samples from a run dir.
  All sample names have been cleaned:
  * library prep has been removed
  * B (reprep), F (fail) suffixes have been removed

  Args:
      rundir (str): FQ path to the run

  Returns (list): a list of sample names
  """
  return get_sample_paths(rundir).keys()

def get_sample_paths(rundir):
  """Associates the samples with their path.
  All sample names have been cleaned:
  * library prep has been removed
  * B (reprep), F (fail) suffixes have been removed

  Args:
      rundir (str): FQ path to the run

  Returns (dict): sample: path

  """
  sample_paths = glob.glob("{rundir}/Unalign*/Project_*/Sample_*".\
    format(rundir=rundir))
  samples = {}
  for sample_path in sample_paths:
    sample = os.path.basename(sample_path).split("_")[1]
    sample = sample.rstrip('BF') # remove the reprep (B) and reception control fail (F) letters from the samplename
    samples[sample] = sample_path
  return samples

def launch_trim(trim_indir, trim_outdir, link_dir, base_dir):
    """Creates sbatch scripts and launches them.
    Last sbatch script will create the 'trimmed.txt' file denoting a succesful run.

    Args:
        trim_indir (str): path to fastq files in need of trimming
        trim_outdir (str): path to output directory
        link_dir (str): path to where trimmed fastq files should be linked to
        base_dir (str): path to where the trimmed.txt file should be written to

    Returns: pass

    """
    script_dir = os.path.join(trim_indir, 'scripts')
    try:
      os.makedirs(script_dir)
    except OSError: pass
    sbatch_ids = []
    for f1 in glob.glob('{}/*_R1_*.fastq.gz'.format(trim_indir)):
      f2 = f1.replace('_R1_', '_R2_')
      f1_filename = os.path.basename(f1)
      f2_filename = os.path.basename(f2)
      outfile = '{}/{}'.format(trim_outdir, os.path.basename(f1).replace('.fastq.gz', ''))
      with tempfile.NamedTemporaryFile(delete=False, dir=script_dir) as sbatch_file:
        sbatch_file.write('#!/bin/bash\n')
        sbatch_file.write('set -e\n')
        sbatch_file.write('java -jar /mnt/hds/proj/bioinfo/SCRIPTS/AgilentReadTrimmer.jar -m1 {f1} -m2 {f2} -o {outfile} -qxt && gzip {outfile}*\n'.format(f1=f1, f2=f2, outfile=outfile))
        sbatch_file.write('mv {outfile}_1.fastq.gz {f1}\n'.format(outfile=outfile, f1=os.path.join(trim_outdir, f1_filename)))
        sbatch_file.write('mv {outfile}_2.fastq.gz {f2}\n'.format(outfile=outfile, f2=os.path.join(trim_outdir, f2_filename)))
        sbatch_file.write('ln -s {f1} {link_dir}/\n'.format(f1=os.path.join(trim_outdir, f1_filename), link_dir=link_dir))
        sbatch_file.write('ln -s {f2} {link_dir}/\n'.format(f2=os.path.join(trim_outdir, f2_filename), link_dir=link_dir))
        sbatch_file.flush()
        try:
          cmd = 'sbatch -A prod001 -t 12:00:00 -J fastqTrimming -c 1 -o {sbatch_output} -e {sbatch_error}'.\
            format(
              sbatch_output='/mnt/hds/proj/bioinfo/LOG/fastqTrimming.%j.out',
              sbatch_error='/mnt/hds/proj/bioinfo/LOG/fastqTrimming.%j.err'
            )
          cl = cmd.split(' ')
          cl.append(sbatch_file.name)
          print(' '.join(cl))
          sbatch_output = subprocess.check_output(cl)
          sbatch_ids.append(sbatch_output.rstrip().split(' ')[-1])
        except subprocess.CalledProcessError, e:
          e.message = "The command {} failed.".format(' '.join(cl))
          raise e

    # once all the jobs succesfully finish, symlink the files back
    with tempfile.NamedTemporaryFile(delete=False, dir=script_dir) as finished_file:
      finished_file.write('#!/bin/bash\n')
      finished_file.write('date +"%Y%m%d%H%M%S" > {}/trimmed.txt\n'.format(base_dir))
      finished_file.flush()
      
      try:
        cmd = "sbatch -A prod001 -t 00:01:00 -J trimmingFinished -c 1 " +\
              "-o {sbatch_output} -e {sbatch_error} --dependency=afterok:{dependencies}".\
                format(
                  sbatch_output='/mnt/hds/proj/bioinfo/LOG/trimmingFinished.%j.out',
                  sbatch_error='/mnt/hds/proj/bioinfo/LOG/trimmingFinished.%j.err',
                  dependencies=':'.join(sbatch_ids)
                )
        cl = cmd.split(' ')
        cl.append(finished_file.name)
        print(' '.join(cl))
        subprocess.check_output(cl)
      except subprocess.CalledProcessError, e:
        e.message = "The command {} failed.".format(' '.join(cl))
        raise e

    pass

def main(argv):
  """Takes one param: the run dir"""
  rundir = argv[0]

  # get all samples of this run
  samples = get_sample_paths(rundir)
  print('Found {} samples: {}'.format(len(samples), samples))
  # determine which samples are QXT
  params = db.readconfig("non")
  for sample, sample_path in samples.items():
    with lims.limsconnect(params['apiuser'], params['apipass'], params['baseuri']) as lmc:
      application_tag = lmc.getattribute('samples', sample, "Sequencing Analysis")
      if application_tag is None:
        print("FATAL: Sequencing application tag not defined for {}".format(sample))
        # skip to the next sample
        continue
      kit_type = application_tag[3:6]
      if kit_type == 'QXT':
        print('Sample {} is QXT! Trimming ...'.format(sample))

        # TODO check in clinstatsdb if this sample is trimmed already ...

        # move the samples to a totrim dir so they don't get picked up by next steps ...
        sample_base_path = os.path.dirname(sample_path)
        trim_dir = sample_base_path + '/totrim'
        outdir   = sample_base_path + '/trimmed'

        fastq_dir = os.path.basename(sample_path)
        fastq_trim_dir = os.path.join(trim_dir, fastq_dir)
        fastq_outdir   = os.path.join(outdir, fastq_dir)

        # skip this sample if the input dir exists
        if os.path.exists(fastq_trim_dir):
          print('{} exists, skipping!'.format(fastq_trim_dir))
          continue
        # skip the sample if output dir not empty
        if os.path.exists(fastq_outdir):
          for dir_path, dir_names, files in os.walk(fastq_outdir):
            if files:
              print('{} not empty, skipping!'.format(fastq_outdir))
              continue

        # create input dir
        try:
          # only create trim_dir, the fastq_dir will me moved in here
          print('mkdir {}'.format(trim_dir))
          os.makedirs(trim_dir)
        except OSError: pass

        # create the output dir
        try:
          print('mkdir {}'.format(fastq_outdir))
          os.makedirs(fastq_outdir)
        except OSError: pass

        # move the fastq files to the totrim dir
        print('mv {} {}'.format(sample_path, trim_dir))
        os.rename(sample_path, fastq_trim_dir)

        # create the original sample dirtory
        try:
          print('mkdir {}'.format(sample_path))
          os.makedirs(sample_path)
        except OSError: pass

        # lauch trim!
        launch_trim(trim_indir=fastq_trim_dir, trim_outdir=fastq_outdir, link_dir=sample_path, base_dir=rundir)

  # mv original samples away
  # mv trimmed samples back, append _trimmed to name

if __name__ == '__main__':
    main(sys.argv[1:])
