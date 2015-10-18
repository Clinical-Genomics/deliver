#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function
import sys

from genologics.lims import *
from genologics.config import BASEURI, USERNAME, PASSWORD

def main(argv):
    lims = Lims(BASEURI, USERNAME, PASSWORD)

    for sample_id in argv:
        try:
            sample = Sample(lims, id=sample_id)
            sample.get(force=True)
        except:
            try:
                print("WARNING: Sample {} not found in LIMS! Trying as CG ID...".format(sample_id), end='')
                # maybe it's an old CG ID
                sample = lims.get_samples(udf={'Clinical Genomics ID': sample_id})[0]
                print("Got it: {}".format(sample.id))
            except:
                print("WARNING: Sample {} still not found in LIMS!".format(sample_id))
                continue

        print(sample.name)

if __name__ == '__main__':
    main(sys.argv[1:])
