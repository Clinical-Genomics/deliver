#!/bin/bash

INDIR=${1?'Provide dir to monitor'}

for MD5SUM_FILE in ${INDIR}/*md5sum; do
    echo $MD5SUM_FILE;
    while read -a MD5SUM_LINE; do
        MD5SUM=${MD5SUM_LINE[0]}
        FASTQ_FILE=${MD5SUM_LINE[1]##*/}

        cd /mnt/hds/proj/bioinfo/git/kenny/data-delivery/
        python -m createlinks.cli cust ${INDIR}/${FASTQ_FILE}
        cd -
    done < $MD5SUM_FILE
done
