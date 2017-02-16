#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc

set -eu

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}


cases=$(scout cases --institute cust002 --finished)
for case in ${cases[@]}; do
    deliver_bamvcfs ${case}
done
