# -*- coding: utf-8 -*-

from deliver.modules.demux import getsamplesfromflowcell

def test_getsamplesfromflowcell():
    demux_dir = 'tests/fixtures/'
    flowcell = 'HB07NADXX'

    assert getsamplesfromflowcell(demux_dir, flowcell) == sorted([
            'SIB910A3', 'SIB914A11', 'SIB914A12', 'SIB914A15',
            'SIB914A2', 'SIB911A1', 'SIB911A2'
            ])
