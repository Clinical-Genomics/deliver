#!/bin/bash

set -eu
shopt -s nullglob

PROJECT_DIR=${1?'Please provide a project directory'}
SAMPLE_TYPE=${2-rnaseq}

DELIVER_DIR=${PROJECT_DIR}/deliver/${SAMPLE_TYPE}/

[[ ! -e ${DELIVER_DIR} ]] && mkdir -p ${DELIVER_DIR}

for FASTQ in ${PROJECT_DIR}/*.fastq.gz; do
    # rename the fastq files so that the sample id is in the front

    FQ=$(basename $FASTQ)
    FQ_DIR=$(dirname $FASTQ)
    IFS='_' read -ra FASTQ_PARTS <<< "${FQ}"
    unset IFS
    SAMPLE_ID=${FASTQ_PARTS[3]}

    [[ ! -e ${DELIVER_DIR}/${SAMPLE_ID} ]] && mkdir ${DELIVER_DIR}/${SAMPLE_ID}

    echo "ln -s ${FASTQ} ${DELIVER_DIR}/${SAMPLE_ID}/barcode_${SAMPLE_ID}_${FQ}"
    ln -s ${FASTQ} ${DELIVER_DIR}/${SAMPLE_ID}/barcode_${SAMPLE_ID}_${FQ}
done
