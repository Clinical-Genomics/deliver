#!/bin/bash

shopt -s expand_aliases
source ~/.bashrc

log() {
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${NOW}] $@"
}


cases=($(housekeeper runs --output case --limit 1000 --after `date +'%Y-%m-%d' -d '15 days ago'`))
for case in "${cases[@]}"; do
    if ! [[ $case =~ cust* ]]; then continue; fi
    log "working on $case"
    cust=${case%%-*}
    if [[ $cust != 'cust002' ]]; then continue; fi
    deliver_bamvcfs ${case}
done
