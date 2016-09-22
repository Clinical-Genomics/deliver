#!/bin/bash

set -e

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}

cd /mnt/hds/proj/bioinfo/git/kenny/data-delivery/
find /mnt/hds/proj/bioinfo/MIP_ANALYSIS/cust002/*/genomes/ -name '*_qc_sampleInfo.yaml' -mdate +1 -mtime -2 -exec python -m createlinks.cli bam $SAMPLE_INFO \;
cd -
