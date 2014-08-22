#!/bin/bash
#
UNABASE=/mnt/hds/proj/bioinfo/DEMUX/
runs=$(ls ${UNABASE})
for run in ${runs[@]}; do
  NOW=$(date +"%Y%m%d%H%M%S")
  if [ -f ${UNABASE}${run}/copycomplete.txt ]; then
    if [ -f ${UNABASE}${run}/delivery.txt ]; then
      echo [${NOW}] [${run}] copy is complete and delivery has already started 
    else
      echo [${NOW}] [${run}] copy is complete delivery has not started
      echo [${NOW}] [${run}] copy is complete delivery is started > ${UNABASE}${run}/delivery.txt 
      sbatch /mnt/hds/proj/bioinfo/SCRIPTS/getfastq.batch ${UNABASE}${run}
    fi
  else
    echo [${NOW}] [${run}] is not yet completely copied
  fi
done
