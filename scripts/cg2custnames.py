#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function
import sys

from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

def read_stats_file(stats_file_name):
    """Reads in the stats file

    Args:
        stats_file_name (str): the FQ file name of the stats file

    Returns (list): one item for each line in the stats file

    """
    with open(stats_file_name, 'r') as stats_file:
        return [ line.rstrip() for line in stats_file.readlines() ]

def get_samples(lines, flowcell):
    """TODO: Docstring for get_sample_names.

    Args:
        lines (list): the lines of a stats file
        flowcell (str): the flowcell name

    Yields: a sample name

    """
    samples = []
    for line in lines:
        if flowcell not in line: # possible header
            continue

        samples.append(line.split('\t')[0])

    return samples

def sanitize_samples(samples):
    """Removes the _nxdual9 index indication

    Args:
        samples (list): a list of sample names

    Yields: a sanitized sample name

    """
    s_samples = []
    for sample in samples:
        s_samples.append(sanitize_sample(sample))

    return s_samples

def sanitize_sample(sample):
    """Removes the _nxdual9 index indication

    Args:
        sample (str): a sample name

    Return (str): a sanitized sample name

    """
    return sample.split('_')[0].rstrip('BF')

def get_flowcell(lines):
    """Gets the flowcell from a stats file

    Args:
        lines (list): the lines in a stats file

    Yields: flowcell name

    """
    flowcells = []
    for line in lines[2:]:
        try:
            flowcell = line.split('\t')[1]
        except:
            continue

        if flowcell not in line: # possible header
            continue

        if flowcell not in flowcells:
            flowcells.append(flowcell)

        yield flowcell

def get_cust_samples(sample_names):
    """Queries LIMS for the cust sample names

    Args:
        **sampe_names (list): a list of sample names (without _nxdual9)

    Returns (dict): key is the sample name. Value is the cust sample name.

    """
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    cust_sample_names = {}

    for sample_name in sample_names:

        cust_sample_names[sample_name] = None

        try:
            sample = Sample(lims, id=sample_name)
            sample.get(force=True)
        except:
            # maybe it's an old CG ID
            sample = lims.get_samples(udf={'Clinical Genomics ID': sample_name})[0]

        cust_sample_names[sample_name] = sample.name

    return cust_sample_names

def main(argv):
    lines = read_stats_file(argv[0])

    flowcell = get_flowcell(lines).next()

    samples      = get_samples(lines, flowcell)
    sane_samples = sanitize_samples(samples)
    cust_samples = get_cust_samples(sane_samples)

    for line in lines:
        if flowcell not in line:
            print(line)

        for sample in samples:
            if sample in line:
                line = line.replace(sample, cust_samples[sanitize_sample(sample)])
                print(line)
                break

if __name__ == '__main__':
    main(sys.argv[1:])
