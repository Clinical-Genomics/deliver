#!/bin/bash

# Renaming script for delivery 273692

INFILE=${1?'Please provide a renaming file'}
INDIR=$(dirname ${INFILE}) # presume the renaming file is in the same dir as the fastq files
RENAMEDDIR=${INDIR}/renamed
INTERNAL_ID=0
EXTERNAL_ID=1

mkdir ${RENAMEDDIR}

while read -a SAMPLE_NAME; do
    for SAMPLE_FILE in ${INDIR}/${SAMPLE_NAME}*; do
        ln -s ${SAMPLE_FILE} ${RENAMEDDIR}/
    done
    rename ${SAMPLE_NAME[${INTERNAL_ID}]} ${SAMPLE_NAME[${EXTERNAL_ID}]} ${RENAMEDDIR}/${SAMPLE_NAME[${INTERNAL_ID}]}*
done < ${INFILE}
