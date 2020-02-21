#!/bin/bash

SET_ENVIRONMENT=${ENVIRONMENT}

shopt -s expand_aliases
source ${HOME}/.bashrc
if [[ ${SET_ENVIRONMENT} == 'production' ]]; then
    useprod
else
    usestage
fi

########
# VARS #
########

HASTA_DEMUXES_DIR=${1-${PROJECT_HOME}/${ENVIRONMENT}/demultiplexed-runs/}
MAILTO=${2-clinical-demux@scilifelab.se} # split on ',' to provide multiple

#############
# FUNCTIONS #
#############

log() {
    local NOW
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[$NOW] $*"
}

failed() {
    echo "Error delivering ${FC}: $(caller)" | mail -s "ERROR delivery ${FC}" "${MAILTO}"
}
trap failed ERR

########
# MAIN #
########

for run in "${HASTA_DEMUXES_DIR}"/*; do
    run=$(basename "$run")
    if [[ -f ${HASTA_DEMUXES_DIR}/${run}/copycomplete.txt ]]; then
        if [[ -f ${HASTA_DEMUXES_DIR}/${run}/delivery.txt ]]; then
            log "${run}" 'copy is complete and delivery has already started'
        else
            log "${run}" 'copy is complete delivery is started' > "${HASTA_DEMUXES_DIR}/${run}/delivery.txt"
            FC=${run##*_}
            FC=${FC:1}

            # add an X FC to clinstatsdb - because the permanent tunnel is not active on the nodes.
            if [[ -d "${HASTA_DEMUXES_DIR}/${run}/l1t11" ]]; then
                log "cgstats add --machine X ${HASTA_DEMUXES_DIR}/${run}"
                cgstats add --machine X "${HASTA_DEMUXES_DIR}/${run}"
                # create stats per project
                for PROJECT in "${HASTA_DEMUXES_DIR}/${run}"/Unaligned/Project*; do
                    PROJECT=$(basename "$PROJECT")
                    PROJECT_NR=${PROJECT##*_}
                    log "cgstats select --project '${PROJECT_NR}' '${FC}' &> '${HASTA_DEMUXES_DIR}/${run}/stats-${PROJECT_NR}-${FC}.txt'"
                         cgstats select --project "${PROJECT_NR}" "${FC}" &> "${HASTA_DEMUXES_DIR}/${run}/stats-${PROJECT_NR}-${FC}.txt"
                done
                # create stats per lane
                log "cgstats lanestats '${HASTA_DEMUXES_DIR}/${run}' &> '${HASTA_DEMUXES_DIR}/${run}/stats.txt'"
                     cgstats lanestats "${HASTA_DEMUXES_DIR}/${run}" &> "${HASTA_DEMUXES_DIR}/${run}/stats.txt"
            fi
            # end add
  
            NOW=$(date +"%Y%m%d%H%M%S")
            cg transfer flowcell "$FC" &> "${HASTA_DEMUXES_DIR}/${run}/cg.transfer.${FC}.${NOW}.log"

            # send an email on completion
            SUBJECT=${FC}
            log "column -t ${HASTA_DEMUXES_DIR}/${run}/stats*.txt | mail -s 'Run ${SUBJECT} COMPLETE!' ${MAILTO}"
            column -t "${HASTA_DEMUXES_DIR}/${run}"/stats*.txt | mail -s "Run ${SUBJECT} COMPLETE!" "${MAILTO}"
        fi
    else
        log "${run}" 'is not yet completely copied'
    fi
done
