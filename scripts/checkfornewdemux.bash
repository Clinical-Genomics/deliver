#!/bin/bash
#

source /mnt/hds/proj/bioinfo/SCRIPTS/log.bash
echo $(getversion)

UNABASE=/mnt/hds/proj/bioinfo/DEMUX/
ALIBASE=/mnt/hds/proj/bioinfo/ALIGN/
runs=$(ls ${UNABASE})
for run in ${runs[@]}; do
  NOW=$(date +"%Y%m%d%H%M%S")
  if [ -f ${UNABASE}${run}/copycomplete.txt ]; then
    if [ -f ${UNABASE}${run}/delivery.txt ]; then
      echo [${NOW}] [${run}] copy is complete and delivery has already started 
    else
      echo [${NOW}] [${run}] copy is complete delivery has not started
      echo [${NOW}] [${run}] copy is complete delivery is started > ${UNABASE}${run}/delivery.txt 
  ## addition 20150219 testing auto summary and linking
      FC=$(echo ${run} | awk 'BEGIN {FS="/"} {split($(NF-1),arr,"_");print substr(arr[4],2,length(arr[4]))}')
      /home/hiseq.clinical/.virtualenvs/develop/bin/python /mnt/hds/proj/bioinfo/SCRIPTS/getsamplesummary.py ${FC} 2>&1 > /mnt/hds/proj/bioinfo/LOG/samplesum.${FC}.${NOW}.log
  ## addition ends
      sbatch /mnt/hds/proj/bioinfo/SCRIPTS/getfastq.batch ${UNABASE}${run}
    fi
#    if [ -d ${ALIBASE}${run}/Aligned ]; then
#      echo [${NOW}] [${run}] copy is complete and alignment has already started 
#    else
#      echo [${NOW}] [${run}] copy is complete alignment has not started
#      sbatch /mnt/hds/proj/bioinfo/SCRIPTS/align.batch ${UNABASE}${run}
#    fi
  else
    echo [${NOW}] [${run}] is not yet completely copied
  fi
done

