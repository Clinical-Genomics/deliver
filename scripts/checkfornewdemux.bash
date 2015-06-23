#!/bin/bash
#

source /mnt/hds/proj/bioinfo/SCRIPTS/log.bash
log $(getversion)

UNABASE=/mnt/hds/proj/bioinfo/DEMUX/
ALIBASE=/mnt/hds/proj/bioinfo/ALIGN/
runs=$(ls ${UNABASE})
for run in ${runs[@]}; do
  if [ -f ${UNABASE}${run}/copycomplete.txt ]; then
    if [ -f ${UNABASE}${run}/delivery.txt ]; then
      log ${run} 'copy is complete and delivery has already started'
    else
      log ${run} 'copy is complete delivery has not started'
      if [ -f ${UNABASE}${run}/trimmed.txt ]; then
        log ${run} 'trimming already finished'
      else
        NOW=$(date +"%Y%m%d%H%M%S")
      	/home/hiseq.clinical/miniconda/envs/prod/bin/python /mnt/hds/proj/bioinfo/SCRIPTS/trimqxt.py ${UNABASE}${run} 2>&1 > ${UNABASE}${run}/trimQXT.${NOW}.log
      fi
      if [ -f ${UNABASE}${run}/trimming.txt ]; then
        log ${run} 'trimming is in progress'
      else
        log ${run} 'copy is complete delivery is started' > ${UNABASE}${run}/delivery.txt 
        FC=$(echo ${run} | awk 'BEGIN {FS="/"} {split($(NF-1),arr,"_");print substr(arr[4],2,length(arr[4]))}')
        NOW=$(date +"%Y%m%d%H%M%S")
        /home/hiseq.clinical/miniconda/envs/prod/bin/python /mnt/hds/proj/bioinfo/SCRIPTS/createfastqlinks.py ${FC} 2>&1 > ${UNABASE}${run}/createfastqlinks.${FC}.${NOW}.log
        sbatch /mnt/hds/proj/bioinfo/SCRIPTS/getfastq.batch ${UNABASE}${run}
      fi
    fi
#    if [ -d ${ALIBASE}${run}/Aligned ]; then
#      log [${run}] copy is complete and alignment has already started 
#    else
#      log [${run}] copy is complete alignment has not started
#      sbatch /mnt/hds/proj/bioinfo/SCRIPTS/align.batch ${UNABASE}${run}
#    fi
  else
    log ${run} 'is not yet completely copied'
  fi
done

