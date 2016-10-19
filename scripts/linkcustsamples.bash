#!/bin/bash

set -e

# check for md5sum file
# for each line in md5sum file

TICKET_FILE=${1?'Please provide a md5sum file: ${ticketID}.md5sum'}
INDIR=$(readlink -f $(dirname "${TICKET_FILE}"))

cd /mnt/hds/proj/bioinfo/git/kenny/data-delivery/
while read -a LINE; do
    MD5SUM=${LINE[0]}
    FASTQ_FILE=${LINE[1]}

    FASTQ_FILE=${FASTQ_FILE##*/}

    echo ${INDIR}/${FASTQ_FILE}

    python -m deliver.cli cust ${INDIR}/${FASTQ_FILE}
done < ${TICKET_FILE}
mv $TICKET_FILE ${TICKET_FILE}_complete
cd -
