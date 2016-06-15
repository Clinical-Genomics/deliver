#!/bin/bash

FILETYPE=TUMOR

for FASTQ in "$@"; do

    FASTQ_DIR=$(dirname $FASTQ)
    FASTQ_FILE=$(basename $FASTQ)

    IFS=_ read -ra FASTQ_PARTS <<< "$FASTQ_FILE"
    unset $IFS # reset IFS

    cd $FASTQ_DIR

    for READ_DIRECTION in 1 2; do
        MH_FASTQ_FILENAME="${FASTQ_PARTS[0]}_${FILETYPE}_${FASTQ_PARTS[2]}_${READ_DIRECTION}"
        MH_FASTQ_FILE="${MH_FASTQ_FILENAME}.fastq.gz"
        LANE1_FASTQ_FILE="${FASTQ_PARTS[0]}_${FASTQ_PARTS[1]}_${FASTQ_PARTS[2]}_L001_R${READ_DIRECTION}_${FASTQ_PARTS[5]}"
        LANE2_FASTQ_FILE="${FASTQ_PARTS[0]}_${FASTQ_PARTS[1]}_${FASTQ_PARTS[2]}_L002_R${READ_DIRECTION}_${FASTQ_PARTS[5]}"

        echo "cat ${FASTQ_DIR}/${LANE1_FASTQ_FILE} ${FASTQ_DIR}/${LANE2_FASTQ_FILE} > ${FASTQ_DIR}/${MH_FASTQ_FILE}"
        cat ${FASTQ_DIR}/${LANE1_FASTQ_FILE} ${FASTQ_DIR}/${LANE2_FASTQ_FILE} > ${FASTQ_DIR}/${MH_FASTQ_FILE}

        echo "md5sum $MH_FASTQ_FILE > ${FASTQ_DIR}/${MH_FASTQ_FILE}.md5"
        md5sum $MH_FASTQ_FILE > ${FASTQ_DIR}/${MH_FASTQ_FILE}.md5

        echo "lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e 'rm -r -f *; put ${MH_FASTQ_FILE}; put ${MH_FASTQ_FILE}.md5; bye;'"
        lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e "rm -r -f *; put ${MH_FASTQ_FILE}; put ${MH_FASTQ_FILE}.md5; bye;"

        echo "rm ${MH_FASTQ_FILE} ${MH_FASTQ_FILE}.md5"
        rm ${MH_FASTQ_FILE} ${MH_FASTQ_FILE}.md5
    done

    echo "touch ${FASTQ_DIR}/${FASTQ_PARTS[0]}_complete"
    touch ${FASTQ_DIR}/${FASTQ_PARTS[0]}_complete

    echo "lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e 'put ${FASTQ_PARTS[0]}_complete; bye;'"
    lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e "put ${FASTQ_PARTS[0]}_complete; bye;"

    echo "rm ${FASTQ_DIR}/${FASTQ_PARTS[0]}_complete"
    rm ${FASTQ_DIR}/${FASTQ_PARTS[0]}_complete
done
