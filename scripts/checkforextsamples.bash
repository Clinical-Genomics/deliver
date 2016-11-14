#!/bin/bash

set -e

EXTDIR=${1?'Please provide the EXTERNAL directory'}

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}

for SAMPLE in ${EXTDIR}/cust*/*; do
    DIR=$(dirname $SAMPLE)
    if [[ -e ${SAMPLE}/delivered.txt ]]; then
        log "Delivered: $SAMPLE"
        continue
    fi

    log "Found: $SAMPLE"

    deliver ext $SAMPLE &>> ${SAMPLE}/project.log
    date +'%Y%m%d%H%M%S' > ${SAMPLE}/delivered.txt
done
