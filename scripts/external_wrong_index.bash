#!/bin/bash

while read FASTQ; do
    TARGET=$(readlink -f $FASTQ)
    if grep -qs EXTERNAL <<< $TARGET; then
        if grep -qsv cust003 <<< $TARGET; then
            echo $FASTQ
            echo $TARGET
            rm $FASTQ
        fi
    fi
done < <(find cust003 -name *fastq.gz)
