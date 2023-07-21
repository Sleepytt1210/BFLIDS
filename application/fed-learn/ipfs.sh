#!/bin/bash

BASE_GATEWAY_PORT=9898
BASE_API_PORT=5001
BASE_SWARM_PORT=4001

if [ -z "$IPFS_PATH" ]; then
    export IPFS_PATH=~/.ipfs && echo "Using default IPFS_PATH=~/.ipfs"
fi

function setup() {

    echo "Setting up IPFS for $ORG"

    if [[ ! -d "$IPFS_PATH" ]]; then
        echo "Initializing IPFS at $IPFS_PATH" && mkdir $IPFS_PATH && cp ${PWD}/../../ipfs-conf/swarm.key "${IPFS_PATH}" && ipfs init
    fi

    ipfs bootstrap rm --all
    ipfs config Addresses.Gateway /ip4/0.0.0.0/tcp/$IPFS_GATEWAY_PORT
    ipfs config Addresses.API /ip4/0.0.0.0/tcp/$IPFS_API_PORT
    ipfs config Addresses.Swarm --json "[\"/ip4/0.0.0.0/tcp/${IPFS_SWARM_PORT}\",\"/ip6/::/tcp/${IPFS_SWARM_PORT}\",\"/ip4/0.0.0.0/udp/${IPFS_SWARM_PORT}/quic\",\"/ip4/0.0.0.0/udp/${IPFS_SWARM_PORT}/quic-v1\",\"/ip4/0.0.0.0/udp/${IPFS_SWARM_PORT}/quic-v1/webtransport\",\"/ip6/::/udp/${IPFS_SWARM_PORT}/quic\",\"/ip6/::/udp/${IPFS_SWARM_PORT}/quic-v1\",\"/ip6/::/udp/${IPFS_SWARM_PORT}/quic-v1/webtransport\"]"
    ipfs daemon
}

function connect() {
    ipfs swarm connect $1
}

function printHelp() {
    println "Usage: `basename ${0}` <command> [args]"
    println "  Commands:"
    println "    setup - To initialise and setup an IPFS daemon."
    println "    connect <address> - To connect to the given IPFS address." 
    println "  Example: `basename ${0}` connect /ip4/104.131.131.82/tcp/4001/p2p/QmaCpDMGvV2BGHeYERUEnRQAwe3N8SzbUtfsmvsqQLuvuJ"
}

function println() {
    echo -e "$1"
}


[[ $# -lt 1 ]] && printHelp && exit


if [[ "$1" == "setup" ]]; then
  setup
elif [[ "$1" == "connect" ]]; then
  ipfs_target="${2}";
  [[ -z "${ipfs_target}" ]] && echo "IPFS connection target is not set!" && printHelp && exit;
  connect "${ipfs_target}";
fi
