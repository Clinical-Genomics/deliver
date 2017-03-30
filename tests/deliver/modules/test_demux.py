# -*- coding: utf-8 -*-

from deliver.modules.demux import getsamplesfromflowcell, getsampleinfofromname_glob

def test_getsamplesfromflowcell():
    demux_dir = 'tests/fixtures/'
    flowcell = 'HB07NADXX'

    assert getsamplesfromflowcell(demux_dir, flowcell) == sorted([
            'SIB910A3', 'SIB914A11', 'SIB914A12', 'SIB914A15',
            'SIB914A2', 'SIB911A1', 'SIB911A2'
            ])

def test_getsampleinfofromname_glob():

    # sample with index name in the sample name: SIB914A11_sureselect11
    demux_dir = 'tests/fixtures/'
    flowcell = 'HB07NADXX'
    sample = 'SIB914A11'

    assert getsampleinfofromname_glob(fc=flowcell, demuxdir=demux_dir, sample=sample) == [
        { 'fc': 'HB07NADXX', 'lane': 1 },
        { 'fc': 'HB07NADXX', 'lane': 2 }
    ]

    # sample without index name in the sample name: SIB910A3
    demux_dir = 'tests/fixtures/'
    flowcell = 'HB07NADXX'
    sample = 'SIB910A3'

    assert getsampleinfofromname_glob(fc=flowcell, demuxdir=demux_dir, sample=sample) == [
        { 'fc': 'HB07NADXX', 'lane': 1 },
        { 'fc': 'HB07NADXX', 'lane': 2 }
    ]
