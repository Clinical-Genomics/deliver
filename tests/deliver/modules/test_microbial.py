# -*- coding: utf-8 -*-

import yaml
from tempfile import mkdtemp
from path import Path

from deliver.modules.microbial import link_microbial

def test_linking():
    microbial_root = Path(mkdtemp())
    demux_root = 'tests/fixtures/'
    sample = 'MIC2407A1'

    config = yaml.load(open('tests/fixtures/config.yaml', 'r'))
    config['demux_root'] = demux_root
    config['microbial_root'] = microbial_root
    link_microbial(config, sample=sample)

    assert microbial_root.joinpath('MIC2407', 'MIC2407A1', 'MIC2407A1_HLJY7BCXY_L1_1.fastq.gz').islink()
    assert microbial_root.joinpath('MIC2407', 'MIC2407A1', 'MIC2407A1_HLJY7BCXY_L1_2.fastq.gz').islink()
    assert microbial_root.joinpath('MIC2407', 'MIC2407A1', 'MIC2407A1_HLJY7BCXY_L2_1.fastq.gz').islink()
    assert microbial_root.joinpath('MIC2407', 'MIC2407A1', 'MIC2407A1_HLJY7BCXY_L2_2.fastq.gz').islink()

    microbial_root.rmdir_p()

test_linking()    
