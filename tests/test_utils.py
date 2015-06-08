# -*- coding: utf-8 -*-
from path import path

from data_delivery import utils


def test_extract_flowcell():
    """Test extraction of flowcell id from run dir path."""
    run_dir = path('/mnt/hds/proj/bioinfo/DEMUX/140812_D00134_0134_BH9BV4ADXX')
    flowcell_id = utils.extract_flowcell(run_dir)

    assert flowcell_id == 'H9BV4ADXX'

    # test with trailing slash
    run_dir = path('/mnt/hds/proj/bioinfo/DEMUX/140108_D00134_0058_AH80JLADXX/')
    flowcell_id = utils.extract_flowcell(run_dir)

    assert flowcell_id == 'H80JLADXX'
