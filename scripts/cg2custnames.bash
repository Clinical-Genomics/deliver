#!/bin/bash
#   usage:
#      cg2custnames.bash     (run in the OUTBOX directory of the flowcell, it should contain the fastqfiles and sampleList.csv)
#
date > renaminglog.txt
metas=$(ls | grep meta)
for meta in ${metas[@]}; do
cp ${meta} ${meta}.bak
awk '{split($1,arr,"_");if (arr[1]=="Sample") {out=arr[2]} else {out=arr[1]};print out,$2,$3,$4,$5,$6,$7}' ${meta} > metatext
mv metatext ${meta}
chmod g+w ${meta}
echo cp ${meta} ${meta}.bak >> renaminglog.txt
sfil=$(ls stats*txt)

cp ${sfil} ${sfil}.bak
echo cp ${sfil} ${sfil}.bak >> renaminglog.txt
awk 'BEGIN {OFS="\t"} {split($1,arr,"_");if (arr[1]=="Sample") {out=arr[2]} else {out=arr[1]};print out,$2,$3,$4,$5,$6,$7,$8,$9}' ${sfil} > wo${sfil}
mv wo${sfil} ${sfil}
chmod g+w ${sfil}
smplists=$(ls | grep sampleList)
for slist in ${smplists[@]}; do
namepairs=$(awk 'BEGIN {FS=","} {if ($1 != "Project") print $3"KLISTERKLISTER"$2}' ${slist})
fastqfiles=$(ls | grep ".fastq.gz$")
for fil in ${fastqfiles[@]};do
  for pair in ${namepairs[@]};do 
#  echo ${pair}
    cgname=$(echo ${pair} | awk 'BEGIN {FS="KLISTERKLISTER"} {print $1}')
#  echo ${cgname}
    cuname=$(echo ${pair} | awk 'BEGIN {FS="KLISTERKLISTER"} {print $2}')
#  echo ${cuname}
#  echo $fastqfiles
    if [[ ${fil} == *${cgname}* ]]; then 
      newname=$(echo ${fil} | sed "s/${cgname}/${cuname}/")
      newname=$(echo ${newname} | sed 's/Sample_//g' | sed 's/_R1/_1/g' | sed 's/_R2/_2/g')
      nnwopn=$(echo ${newname} | awk 'BEGIN {FS="_";OFS="_"} {if ($7!="") print $1,$2,$3,$4,$6,$7}')
      if [ ! -z ${nnwopn} ]; then
        newname=${nnwopn}
      fi
      sed -i "s/${fil}/${newname}/g" ${meta}
      echo sed -i "s/${fil}/${newname}/g" ${meta} >> renaminglog.txt
    fi
#    echo ${fil} ${newname} 
  done
  mv ${fil} ${newname} 
  echo mv ${fil} ${newname} >> renaminglog.txt
#  echo ${fil} ${nnwopn}
done


for pair in ${namepairs[@]};do
  cgname=$(echo ${pair} | awk 'BEGIN {FS="KLISTERKLISTER"} {print $1}')
  cuname=$(echo ${pair} | awk 'BEGIN {FS="KLISTERKLISTER"} {print $2}')
  sed -i "s/${cgname}/${cuname}/g" ${sfil}
  echo sed -i "s/${cgname}/${cuname}/g" ${sfil} >> renaminglog.txt
  sed -i "s/${cgname}/${cuname}/g" ${meta}
  echo sed -i "s/${cgname}/${cuname}/g" ${meta} >> renaminglog.txt
done

done

done
