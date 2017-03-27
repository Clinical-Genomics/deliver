#!/bin/bash

PROJECT_DIR=${1?'Please provide a project directory'}

DELIVER_DIR=${PROJECT_DIR}/deliver/wgs/

[[ ! -e ${DELIVER_DIR} ]] && mkdir -p ${DELIVER_DIR}

for FASTQ in ${PROJECT_DIR}/*.vcf ${PROJECT_DIR}/*.bcf ${PROJECT_DIR}/*/*.bam*; do
    # rename the fastq files so that the sample id is in the front

    FQ=$(basename $FASTQ)
    FQ_DIR=$(dirname $FASTQ)
    IFS='_' read -ra FASTQ_PARTS <<< "${FQ}"
    SAMPLE_ID=${FASTQ_PARTS[0]}
    SAMPLE_ID=${SAMPLE_ID%%fam}
    unset IFS

    [[ ! -e ${DELIVER_DIR}/${SAMPLE_ID} ]] && mkdir ${DELIVER_DIR}/${SAMPLE_ID}

    echo "ln -s ${FASTQ} ${DELIVER_DIR}/${SAMPLE_ID}/barcode_${SAMPLE_ID}_${FQ}"
    ln -s ${FASTQ} ${DELIVER_DIR}/${SAMPLE_ID}/barcode_${SAMPLE_ID}_${FQ}
done
