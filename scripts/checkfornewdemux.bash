#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc

########
# VARS #
########

MAILTO=bioinfo.clinical@scilifelab.se,anna.leinfelt@scilifelab.se,emilia.ottosson@scilifelab.se
ERROR_EMAIL=kenny.billiau@scilifelab.se
UNABASE=/mnt/hds/proj/bioinfo/DEMUX/
runs=$(ls ${UNABASE})

#############
# FUNCTIONS #
#############

log() {
    local NOW=$(date +"%Y%m%d%H%M%S")
    echo "[$NOW] $@"
}

failed() {
    echo ${FC} | mail -s "ERROR delivery ${FC}" ${EMAIL}
}
trap failed ERR

########
# MAIN #
########

for run in ${runs[@]}; do
    if [ -f ${UNABASE}${run}/copycomplete.txt ]; then
        if [ -f ${UNABASE}${run}/delivery.txt ]; then
            log ${run} 'copy is complete and delivery has already started'
        else
            log ${run} 'copy is complete delivery is started' > ${UNABASE}${run}/delivery.txt
            FC=$(echo ${run} | awk 'BEGIN {FS="/"} {split($(NF-1),arr,"_");print substr(arr[4],2,length(arr[4]))}')
  
            # add an X FC to clinstatsdb - because the permanent tunnel is not active on the nodes.
            if [[ -d "${UNABASE}${run}/l1t11" ]]; then
                cgstats add --machine X ${UNABASE}${run}
                # create stats per project
                for PROJECT in ${UNABASE}${run}/Unaligned/Project*; do
                    PROJECT=$(basename $PROJECT)
                    PROJECT_NR=${PROJECT##*_}
                    cgstats select --project ${PROJECT_NR} ${FC} &> ${UNABASE}${run}/stats-${PROJECT_NR}-${FC}.txt
                done
                # create stats per lane
                cgstats lanestats ${UNABASE}${run} &> ${UNABASE}${run}/stats.txt
            fi
            # end add
  
            # link the fastq files to MIP_ANALYSIS
            NOW=$(date +"%Y%m%d%H%M%S")
            deliver mip --flowcell $FC &> ${UNABASE}${run}/createfastqlinks.${FC}.${NOW}.log
            deliver microbial --flowcell $FC &> ${UNABASE}${run}/microbial.${FC}.${NOW}.log
  
            # link the fastq files to cust/INBOX
            deliver_fastqs_fc ${FC}
  
            SUBJECT=${FC}
            # send an email on completion
            log "column -t ${UNABASE}${run}/stats*.txt | mail -s 'Run ${SUBJECT} COMPLETE!' ${MAILTO}"
            column -t ${UNABASE}${run}/stats*.txt | mail -s "Run ${SUBJECT} COMPLETE!" ${MAILTO}
        fi
    else
        log ${run} 'is not yet completely copied'
    fi
done
