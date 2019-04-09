#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc

########
# VARS #
########

MAILTO=clinical-demux@scilifelab.se
ERROR_EMAIL=clinical-demux@scilifelab.se
UNABASE=/mnt/hds/proj/bioinfo/DEMUX/
HASTA_DEMUXES_DIR=/home/proj/production/demultiplexed-runs/

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

for run in ${UNABASE}/*; do
    run=$(basename $run)
    if [[ -f ${UNABASE}${run}/copycomplete.txt ]]; then
        if [[ -f ${UNABASE}${run}/delivery.txt ]]; then
            log ${run} 'copy is complete and delivery has already started'
        else
            log ${run} 'copy is complete delivery is started' > ${UNABASE}${run}/delivery.txt
            FC=$(echo ${run} | awk 'BEGIN {FS="/"} {split($(NF-1),arr,"_");print substr(arr[4],2,length(arr[4]))}')
  
            # add an X FC to clinstatsdb - because the permanent tunnel is not active on the nodes.
            if [[ -d "${UNABASE}${run}/l1t11" ]]; then
                log "cgstats add --machine X ${UNABASE}${run}"
                cgstats add --machine X ${UNABASE}${run}
                # create stats per project
                for PROJECT in ${UNABASE}${run}/Unaligned/Project*; do
                    PROJECT=$(basename $PROJECT)
                    PROJECT_NR=${PROJECT##*_}
                    log "cgstats select --project ${PROJECT_NR} ${FC} &> ${UNABASE}${run}/stats-${PROJECT_NR}-${FC}.txt"
                    cgstats select --project ${PROJECT_NR} ${FC} &> ${UNABASE}${run}/stats-${PROJECT_NR}-${FC}.txt
                done
                # create stats per lane
                log "cgstats lanestats ${UNABASE}${run} &> ${UNABASE}${run}/stats.txt"
                cgstats lanestats ${UNABASE}${run} &> ${UNABASE}${run}/stats.txt
            fi
            # end add
  
            NOW=$(date +"%Y%m%d%H%M%S")
            deliver microbial --flowcell $FC &> ${UNABASE}${run}/microbial.${FC}.${NOW}.log
  
            # post X action: copy to hasta
            if [[ -d "${UNABASE}${run}/l1t11" ]]; then
                log "rsync -rvtl ${UNABASE}${run} hasta:${HASTA_DEMUXES_DIR}"
                rsync -rvtl ${UNABASE}${run} hasta:${HASTA_DEMUXES_DIR}
                log "ssh hasta \"find -L ${HASTA_DEMUXES_DIR}/${run} -type l -printf 'ln -sf %l %h/%f\n' | sed s'|${UNABASE}|${HASTA_DEMUXES_DIR}|' | sh\""
                ssh hasta "find -L ${HASTA_DEMUXES_DIR}/${run} -type l -printf 'ln -sf %l %h/%f\n' | sed s'|${UNABASE}|${HASTA_DEMUXES_DIR}|' | sh"
                log "ssh hasta \"rm ${HASTA_DEMUXES_DIR}/${run}/delivery.txt\""
                ssh hasta "rm ${HASTA_DEMUXES_DIR}/${run}/delivery.txt"
            fi
        fi
    else
        log ${run} 'is not yet completely copied'
    fi
done
