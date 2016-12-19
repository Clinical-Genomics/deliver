#!/bin/bash

set -e

INDIR=${1?'Please provide the md5sum directory'}
SCRIPTDIR=$(dirname $0)

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}

for MD5SUM_FILE in ${INDIR}/*md5sum; do
    log "Found: $MD5SUM_FILE"
    bash ${SCRIPTDIR}/linkcustsamples.bash ${MD5SUM_FILE}
done
