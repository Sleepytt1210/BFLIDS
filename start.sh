#!/bin/bash

. network/scripts/utils.sh

function checkPrerequisites(){
    declare -A commands=(
        docker
        ipfs
        python
        node
        jq
    )
    # Check docker 
    for i in ${commands[@]}; do

        $i --version > /dev/null 2>&1

        if [[ $? -ne 0 ]]; then
            errorln "$i command not found..."
            errorln
            [[ "$i" == 'docker' ]] && errorln "Please ensure Docker Desktop is running if you are using WSL2."
            errorln "Follow the instructions in README to install the prerequisites."
            exit 1
        fi
    done
}

checkPrerequisites

# Quick start network
# Ensure no network is running at the moment
network/network.sh down

network/network.sh up -ca

network/network.sh createChannel -c fedlearn

network/network.sh deployCC -c fedlearn -ccn fedLearn -ccp ../chaincodes/federatedLearning -ccl typescript

