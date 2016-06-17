#!/bin/bash

source /mnt/hds/proj/bioinfo/SCRIPTS/log.bash
log $(getversion)

MAILTO=bioinfo.clinical@scilifelab.se,anna.zetterlund@scilifelab.se,anna.leinfelt@scilifelab.se,emilia.ottosson@scilifelab.se
UNABASE=/mnt/hds/proj/bioinfo/DEMUX/
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
        python /mnt/hds/proj/bioinfo/SCRIPTS/trimqxt.py ${UNABASE}${run} &> ${UNABASE}${run}/trimQXT.${NOW}.log
      fi

      if [ ! -f ${UNABASE}${run}/trimming.txt ]; then
        log ${run} 'copy is complete delivery is started' > ${UNABASE}${run}/delivery.txt
        FC=$(echo ${run} | awk 'BEGIN {FS="/"} {split($(NF-1),arr,"_");print substr(arr[4],2,length(arr[4]))}')

        # add an X FC to clinstatsdb - because the permanent tunnel is not active on the nodes.
        if [[ "${FC}" == *CCXX ]]; then
          log ${run} "python /mnt/hds/proj/bioinfo/SCRIPTS/xparseunaligned.py ${UNABASE}${run} &> ${UNABASE}${run}/LOG/xparseunaligned.`date +'%Y%m%d%H%M%S'`.log"
          python /mnt/hds/proj/bioinfo/SCRIPTS/xparseunaligned.py ${UNABASE}${run} &> ${UNABASE}${run}/LOG/xparseunaligned.`date +'%Y%m%d%H%M%S'`.log

          # create stats per project
          for PROJECT in ${UNABASE}${run}/Unaligned/Project*; do
            PROJECT=$(basename $PROJECT)
            PROJECT_NR=${PROJECT##*_}
            log ${run} "python /mnt/hds/proj/bioinfo/SCRIPTS/selectdemux.py $PROJECT_NR $FC &> ${UNABASE}${run}/stats-${PROJECT_NR}-${FC}.txt"
            python /mnt/hds/proj/bioinfo/SCRIPTS/selectdemux.py $PROJECT_NR $FC &> ${UNABASE}${run}/stats-${PROJECT_NR}-${FC}.txt
          done
        fi
        # end add

        NOW=$(date +"%Y%m%d%H%M%S")
        python /mnt/hds/proj/bioinfo/SCRIPTS/createfastqlinks.py ${FC} &> ${UNABASE}${run}/createfastqlinks.${FC}.${NOW}.log

        SUBJECT=${FC}
        # send an email on completion
        log "column -t ${UNABASE}${run}/stats*.txt | mail -s 'Run ${SUBJECT} COMPLETE!' ${MAILTO}"
        column -t ${UNABASE}${run}/stats*.txt | mail -s "Run ${SUBJECT} COMPLETE!" ${MAILTO}
      fi
    fi
  else
    log ${run} 'is not yet completely copied'
  fi
done
