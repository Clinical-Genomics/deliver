#!/bin/bash

EXTDIR=${1?'Please provide the EXTERNAL directory'}

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}

cd /mnt/hds/proj/bioinfo/git/kenny/data-delivery/
for SAMPLE in ${EXTDIR}/*; do
    DIR=$(dirname $SAMPLE)
    if [[ -e ${DIR}/delivered.txt ]]; then
        log "Delivered: $SAMPLE"
        continue
    fi

    log "Found: $SAMPLE"

    python -m createlinks.cli ext $SAMPLE
    date +'%Y%m%d%H%M%S' > ${DIR}/delivered.txt
done
cd -
