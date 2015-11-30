#!/bin/bash

source /mnt/hds/proj/bioinfo/SCRIPTS/log.bash
log $(getversion)

MAILTO=kenny.billiau@scilifelab.se,emma.sernstad@scilifelab.se,daniel.backman@scilifelab.se
UNABASE=/mnt/hds/proj/bioinfo/DEMUX/
ALIBASE=/mnt/hds/proj/bioinfo/ALIGN/
runs=$(ls ${UNABASE})
for run in ${runs[@]}; do
  if [ -f ${UNABASE}${run}/copycomplete.txt ]; then
    if [ -f ${UNABASE}${run}/delivery.txt ]; then
      log ${run} 'copy is complete and delivery has already started'
    else
      if [ -f ${UNABASE}${run}/trimmed.txt ]; then
        log ${run} 'trimming already finished'
      elif [ -f ${UNABASE}${run}/trimming.txt ]; then
        log ${run} 'trimming is in progress'
      else
        log ${run} 'start trimming ...'
        NOW=$(date +"%Y%m%d%H%M%S")
      	/home/hiseq.clinical/miniconda/envs/prod/bin/python /mnt/hds/proj/bioinfo/SCRIPTS/trimqxt.py ${UNABASE}${run} &> ${UNABASE}${run}/trimQXT.${NOW}.log
      fi

      if [ ! -f ${UNABASE}${run}/trimming.txt ]; then
        log ${run} 'copy is complete delivery is started' > ${UNABASE}${run}/delivery.txt 
        FC=$(echo ${run} | awk 'BEGIN {FS="/"} {split($(NF-1),arr,"_");print substr(arr[4],2,length(arr[4]))}')
        NOW=$(date +"%Y%m%d%H%M%S")
        /home/hiseq.clinical/miniconda/envs/prod/bin/python /mnt/hds/proj/bioinfo/SCRIPTS/createfastqlinks.py ${FC} &> ${UNABASE}${run}/createfastqlinks.${FC}.${NOW}.log


	SUBJECT=${FC}
	# send an email on completion
	log "cat ${UNABASE}${run}/stats*.txt | mail -s 'Run ${SUBJECT} COMPLETE!' ${MAILTO}"
	cat ${UNABASE}${run}/stats*.txt | mail -s "Run ${SUBJECT} COMPLETE!" ${MAILTO}
      fi
    fi
  else
    log ${run} 'is not yet completely copied'
  fi
done
