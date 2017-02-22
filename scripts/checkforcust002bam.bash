#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc

set -eu

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}


cases=$(housekeeper runs --output case --limit 1000 --after `date +'%Y-%m-%d' -d '15 days ago'`)
for case in ${cases[@]}; do
    case=${case%% - *}
    cust=${case%%-*}
    if [[ $cust != 'cust002' ]]; then continue; fi
    deliver_bamvcfs ${case}
done
