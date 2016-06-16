#!/bin/bash

EXTDIR=${1?'Please provide the EXTERNAL directory'}

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}

cd /mnt/hds/proj/bioinfo/git/kenny/data-delivery/
for SAMPLE in ${EXTDIR}/*; do
    log "Found: $SAMPLE"

    python -m createlinks.cli ext $SAMPLE
done
cd -
