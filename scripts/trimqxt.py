#!/usr/bin/env python
# encoding: utf-8

import sys
import glob
import os
import subprocess
import tempfile
from access import db, lims

def get_sample_names(rundir):
  """TODO: Docstring for getsamplesfromrun.

  Args:
      rundir (TODO): TODO

  Returns: TODO
  """
  return get_sample_paths(rundir).keys()

def get_sample_paths(rundir):
  """TODO: Docstring for get_sample_paths.

  Args:
      rundir (TODO): TODO

  Returns (dict): sample: path

  """
  sample_paths = glob.glob("{rundir}/Unalign*/Project_*/Sample_*".\
    format(rundir=rundir))
  samples = {}
  for sample_path in sample_paths:
    sample = sample_path.split("/")[-1].split("_")[1]
    sample = sample.rstrip('BF') # remove the reprep (B) and reception control fail (F) letters from the samplename
    samples[sample] = sample_path
  return samples

def launch_trim(indir, outdir, base_path):
    """TODO: Docstring for launch_trim

    Args:
        arg1 (TODO): TODO

    Returns: TODO

    """
    script_dir = os.path.join(indir, 'scripts')
    try:
      os.makedirs(script_dir)
    except OSError: pass
    for f1 in glob.glob('{}/*_R1_*.fastq.gz'.format(indir)):
      f2 = f1.replace('_R1_', '_R2_')
      f1_filename = os.path.basename(f1)
      f2_filename = os.path.basename(f2)
      outfile = '{}/{}'.format(outdir, os.path.basename(f1).replace('.fastq.gz', ''))
      with tempfile.NamedTemporaryFile(delete=False, dir=script_dir) as sbatch_file:
        sbatch_file.write('#!/bin/bash\n')
        sbatch_file.write('java -jar /mnt/hds/proj/bioinfo/SCRIPTS/AgilentReadTrimmer.jar -m1 {f1} -m2 {f2} -o {outfile} -qxt && gzip {outfile}*\n'.format(f1=f1, f2=f2, outfile=outfile))
        sbatch_file.write('mv {outfile}_1.fastq.gz {f1}\n'.format(outfile=outfile, f1=os.path.join(outdir, f1_filename)))
        sbatch_file.write('mv {outfile}_2.fastq.gz {f2}\n'.format(outfile=outfile, f2=os.path.join(outdir, f2_filename)))
        sbatch_file.write('ln -s {f1} {indir}\n'.format(f1=os.path.join(outdir, f1_filename), indir=indir))
        sbatch_file.write('ln -s {f2} {indir}\n'.format(f2=os.path.join(outdir, f2_filename), indir=indir))
        sbatch_file.write('date +"%Y%m%d%H%M%S" > {}/trimmed.txt\n')
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
          subprocess.Popen(cl)
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
        sample_path_split = sample_path.split('/')
        sample_base_path = '/'.join(sample_path_split[0:-1]) 
        trim_dir = sample_base_path + '/totrim'
        outdir   = sample_base_path + '/trimmed'
        fastq_dir = sample_path_split[-1]
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

        # lauch trim!
        launch_trim(fastq_trim_dir, fastq_outdir, sample_base_path)

  # mv original samples away
  # mv trimmed samples back, append _trimmed to name

if __name__ == '__main__':
    main(sys.argv[1:])
