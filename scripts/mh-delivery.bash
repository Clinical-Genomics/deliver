#!/bin/bash

set -e

FILETYPE=TUMOR

FASTQ_DIR=${1?'Please provide a sample directory.'}

if [[ -f $FASTQ_DIR ]]; then
    echo >&2 "'${FASTQ_DIR}' is a file, not a directory. Aborting."
    exit 1
fi

# get one fastq file to determine induvidual parts of MH-fastq file name
for FASTQ in ${FASTQ_DIR}/*_1.fastq.gz; do
    FASTQ_FILE=$(basename $FASTQ)

    IFS=_ read -ra FASTQ_PARTS <<< "$FASTQ_FILE"
    unset IFS # reset IFS

    LANE=${FASTQ_PARTS[0]}
    DATE=${FASTQ_PARTS[1]}
    FC=${FASTQ_PARTS[2]}
    SAMPLE=${FASTQ_PARTS[3]}
    INDEX=${FASTQ_PARTS[4]}
    break
done

cd $FASTQ_DIR

for READ_DIRECTION in 1 2; do

    # create the MH file name
    MH_FASTQ_FILENAME="${SAMPLE}_${FILETYPE}_${INDEX}_${READ_DIRECTION}"
    MH_FASTQ_FILE="${MH_FASTQ_FILENAME}.fastq.gz"
    FASTQ_FILES="*_${READ_DIRECTION}.fastq.gz"

    # create the MH file
    echo "cat ${FASTQ_DIR}/${FASTQ_FILES} > ${FASTQ_DIR}/${MH_FASTQ_FILE}"
    cat ${FASTQ_DIR}/${FASTQ_FILES} > ${FASTQ_DIR}/${MH_FASTQ_FILE}

    # md5sum the MH file
    echo "md5sum $MH_FASTQ_FILE > ${FASTQ_DIR}/${MH_FASTQ_FILE}.md5"
    md5sum $MH_FASTQ_FILE > ${FASTQ_DIR}/${MH_FASTQ_FILE}.md5

    # upload the MH file and md5sum
    echo "lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e 'put ${MH_FASTQ_FILE}; put ${MH_FASTQ_FILE}.md5; bye;'"
    lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e "put ${MH_FASTQ_FILE}; put ${MH_FASTQ_FILE}.md5; bye;"

    # only remove the generated fastq.gz file so we have proof of what we uploaded
    echo "rm ${MH_FASTQ_FILE}"
    rm ${MH_FASTQ_FILE}
done

# signal completion
echo "touch ${FASTQ_DIR}/${SAMPLE}_complete"
touch ${FASTQ_DIR}/${SAMPLE}_complete

echo "lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e 'put ${SAMPLE}_complete; bye;'"
lftp sftp://SFL:@ftp.de.molecularhealth.com/upload/ -e "put ${SAMPLE}_complete; bye;"

# don't remove the _complete file to signal we have delivered
