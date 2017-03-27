#!/bin/bash
#SBATCH -t 8:00:00
#SBATCH -c 2
#SBATCH -A prod001
#SBATCH -J SCAPIS_gpg
##SBATCH --qos=high
#SBATCH --output=/mnt/hds/proj/bioinfo/LOG/scapis-%j.out
#SBATCH --error=/mnt/hds/proj/bioinfo/LOG/scapis-%j.err
##SBATCH --mail-type=END
##SBATCH --mail-user=kenny.billiau@scilifelab.se

set -ue -o pipefail
shopt -s nullglob

PROJECT_DIR=${1?'Please provide a project directory'}
DELIVER_DIR=${PROJECT_DIR}

read -s -p "Passphrase: " PASSPHRASE

#for FASTQ in ${PROJECT_DIR}/*/*fastq.gz; do
for FASTQ in ${PROJECT_DIR}/*.gz; do
    # take care of interruptions
    if [[ -e ${FASTQ} && -e ${FASTQ}.gpg ]]; then
        echo "rm ${FASTQ}.gpg"
        rm ${FASTQ}.gpg
    fi

    # if done skip ...
    if [[ -e ${FASTQ}.gpg ]]; then
        echo "Skipping ${FASTQ}"
        continue
    fi

    # GO!
    FASTQ_DIR=$(dirname ${FASTQ})
    FASTQ_FILE=$(basename ${FASTQ})

    mkdir -p $TMPDIR
    cp ${FASTQ} ${TMPDIR}/

    NODE_FASTQ=${TMPDIR}/${FASTQ_FILE}

    # encrypt
    echo "gpg -e -r 'Kalle von Feilitzen' --yes -o ${NODE_FASTQ}.gpg ${NODE_FASTQ}"
    gpg -e -r "Kalle von Feilitzen" --yes -o ${NODE_FASTQ}.gpg ${NODE_FASTQ}

    # check of encryption was successful
    echo "cat ${NODE_FASTQ} | md5sum &"
    ORI_MD5=$(cat ${NODE_FASTQ} | md5sum &)

    echo "gpg --batch --passphrase -d ${NODE_FASTQ}.gpg | md5sum"
    DECRYPT_MD5=$(gpg --batch --passphrase ${PASSPHRASE} -d ${NODE_FASTQ}.gpg | md5sum)

    if [[ ${DECRYPT_MD5} != $ORI_MD5 ]]; then
        ( >&2 echo "ERROR: ${NODE_FASTQ} ENCRYPTION FAIL" )
        exit 1
    fi

    # finish up
    echo "cp ${NODE_FASTQ}.gpg ${FASTQ_DIR}"
    cp ${NODE_FASTQ}.gpg ${FASTQ_DIR}
    echo "rm ${FASTQ}"
    rm ${FASTQ}
done
