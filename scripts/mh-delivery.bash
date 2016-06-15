#!/bin/bash

FILETYPE=TUMOR

for FASTQ in "$@"; do

    FASTQ_DIR=$(dirname $FASTQ)
    FASTQ_FILE=$(basename $FASTQ)

    IFS=_ read -ra FASTQ_PARTS <<< "$FASTQ_FILE"
    unset $IFS # reset IFS

    LANE=${FASTQ_PARTS[0]}
    DATE=${FASTQ_PARTS[1]}
    FC=${FASTQ_PARTS[2]}
    SAMPLE=${FASTQ_PARTS[3]}
    INDEX=${FASTQ_PARTS[4]}

    cd $FASTQ_DIR

    for READ_DIRECTION in 1 2; do

        if [[ $FASTQ_FILE =~ *_2.fastq.gz ]]; then continue; fi

        MH_FASTQ_FILENAME="${SAMPLE}_${FILETYPE}_${INDEX}_${READ_DIRECTION}"
        MH_FASTQ_FILE="${MH_FASTQ_FILENAME}.fastq.gz"
        FASTQ_FILES="*_${DATE}_${FC}_${FC}_${SAMPLE}_${INDEX}_${READ_DIRECTION}.fastq.gz"

        echo "cat ${FASTQ_DIR}/${FASTQ_FILES} > ${FASTQ_DIR}/${MH_FASTQ_FILE}"
        cat ${FASTQ_DIR}/${LANE1_FASTQ_FILE} ${FASTQ_DIR}/${LANE2_FASTQ_FILE} > ${FASTQ_DIR}/${MH_FASTQ_FILE}

        echo "md5sum $MH_FASTQ_FILE > ${FASTQ_DIR}/${MH_FASTQ_FILE}.md5"
        md5sum $MH_FASTQ_FILE > ${FASTQ_DIR}/${MH_FASTQ_FILE}.md5

        echo "lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e 'put ${MH_FASTQ_FILE}; put ${MH_FASTQ_FILE}.md5; bye;'"
        lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e "put ${MH_FASTQ_FILE}; put ${MH_FASTQ_FILE}.md5; bye;"

        echo "rm ${MH_FASTQ_FILE} ${MH_FASTQ_FILE}.md5"
        rm ${MH_FASTQ_FILE} ${MH_FASTQ_FILE}.md5
    done

    echo "touch ${FASTQ_DIR}/${SAMPLE}_complete"
    touch ${FASTQ_DIR}/${SAMPLE}_complete

    echo "lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e 'put ${SAMPLE}_complete; bye;'"
    lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e "put ${SAMPLE}_complete; bye;"

    echo "rm ${FASTQ_DIR}/${SAMPLE}_complete"
    rm ${FASTQ_DIR}/${SAMPLE}_complete
done
