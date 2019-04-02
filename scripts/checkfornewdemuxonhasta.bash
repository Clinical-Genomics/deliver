#!/bin/bash

shopt -s expand_aliases
source ${HOME}/.bashrc
useprod

########
# VARS #
########

ERROR_EMAIL=clinical-demux@scilifelab.se
HASTA_DEMUXES_DIR=${PROJECT_HOME}/${ENVIRONMENT}/demultiplexed-runs/

#############
# FUNCTIONS #
#############

log() {
    local NOW=$(date +"%Y%m%d%H%M%S")
    echo "[$NOW] $@"
}

failed() {
    echo "Error delivering ${FC}: $(caller)" | mail -s "ERROR delivery ${FC}" ${ERROR_EMAIL}
}
trap failed ERR

########
# MAIN #
########

for run in ${HASTA_DEMUXES_DIR}/*; do
    run=$(basename $run)
    if [[ -f ${HASTA_DEMUXES_DIR}${run}/copycomplete.txt ]]; then
        if [[ -f ${HASTA_DEMUXES_DIR}${run}/delivery.txt ]]; then
            log ${run} 'copy is complete and delivery has already started'
        else
            log ${run} 'copy is complete delivery is started' > ${HASTA_DEMUXES_DIR}${run}/delivery.txt
            FC=$(echo ${run} | awk 'BEGIN {FS="/"} {split($(NF-1),arr,"_");print substr(arr[4],2,length(arr[4]))}')
  
            NOW=$(date +"%Y%m%d%H%M%S")
            cg transfer flowcell $FC &> ${HASTA_DEMUXES_DIR}${run}/cg.transfer.${FC}.${NOW}.log
        fi
    else
        log ${run} 'is not yet completely copied'
    fi
done
