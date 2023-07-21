#!/bin/bash
export PATH=${PWD}/bin:$PATH
export FABRIC_CFG_PATH=$PWD/config/

function asOrg() {
    echo "Using ${ORG}"
    ORDERER_CA=${PWD}/network/organizations/ordererOrganizations/example.com/tlsca/tlsca.example.com-cert.pem
    PEER0_ORG_CA=${PWD}/network/organizations/peerOrganizations/${ORG}.example.com/tlsca/tlsca.${ORG}.example.com-cert.pem
    CORE_PEER_LOCALMSPID=Org1MSP
    CORE_PEER_MSPCONFIGPATH=${PWD}/network/organizations/peerOrganizations/${ORG}.example.com/users/Admin@${ORG}.example.com/msp
    CORE_PEER_ADDRESS=localhost:7051
    CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/network/organizations/peerOrganizations/${ORG}.example.com/tlsca/tlsca.${ORG}.example.com-cert.pem

    export CORE_PEER_TLS_ENABLED=true
    export ORDERER_CA="${ORDERER_CA}"
    export PEER0_ORG_CA="${PEER0_ORG_CA}"

    export CORE_PEER_MSPCONFIGPATH="${CORE_PEER_MSPCONFIGPATH}"
    export CORE_PEER_ADDRESS="${CORE_PEER_ADDRESS}"
    export CORE_PEER_TLS_ROOTCERT_FILE="${CORE_PEER_TLS_ROOTCERT_FILE}"

    export CORE_PEER_LOCALMSPID="${CORE_PEER_LOCALMSPID}"
}

function invoke() {
    if [[ -z $3 ]]; then
        ARGS=''
    else
        ARGS=", $(echo $3 | sed 's/[^[:space:],]\+/"&"/g')"
    fi
    set -x;
    peer chaincode invoke --orderer "0.0.0.0:7050" --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -C fedlearn -n fedLearn --peerAddresses $CORE_PEER_ADDRESS --tlsRootCertFiles $CORE_PEER_TLS_ROOTCERT_FILE --peerAddresses localhost:9051 --tlsRootCertFiles "${PWD}/network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt" -c "{\"Args\":[\"$1:$2\"${ARGS}]}"
    { set +x; } 2>/dev/null
}

function query() {
    if [[ -z $3 ]]; then
        ARGS=''
    else
        ARGS=", $(echo $3 | sed 's/[^[:space:],]\+/"&"/g')"
    fi
    set -x;
    peer chaincode query --orderer "0.0.0.0:7050" --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -C fedlearn -n fedLearn -c "{\"Args\":[\"$1:$2\"${ARGS}]}"
    { set +x; } 2>/dev/null
}

function printHelp() {
    println "Usage: `basename ${0}` <command> [args]"
    println "  Commands:"
    println "    invoke - To invoke the fedLearn chaincode as a peer."
    println "    query - To query the fedLearn chaincode as a peer." 
    println "  Flags:" 
    println "    -c <contract_name> Contract name to be used." 
    println "    -f <func_name>     Function name to be called." 
    println "    -u <org_name>      Organization name (e.g. org1, org2...)." 
    println "    -a <args>          Arguments to be passed into a function, put an empty string if None." 
    println "  Example: `basename ${0}` invoke -c GlobalLearningContract -f CreateCheckpoint -u org1 -a \"model_r1, model_r1_hash, ipfs.com/somehash, User1@org1.example.com, BiLSTM, 93.7, 93.7, 93.7, 1\""
}

function println() {
    echo -e "$1"
}

if [[ $# -lt 1 ]]; then
    printHelp
    exit 1
else    
    COMMAND=$1
    shift
fi

while getopts ":c:f:u:a:" opt; do
    case ${opt} in
    c )
        CONTRACT_NAME=$OPTARG
        ;;
    f )
        FUNCTION_NAME=$OPTARG
        ;;
    u ) 
        ORG=${OPTARG:-org1}
        ;;
    a ) 
        FUNC_ARGS+=("$OPTARG")
        ;;
    \? )
        echo "Invalid Option: -$OPTARG" 1>&2
        exit 1
        ;;
    : )
        echo "Invalid Option: -$OPTARG requires an argument" 1>&2
        exit 1
        ;;
    esac
done
shift $((OPTIND -1))
asOrg

case "$COMMAND" in
    invoke)
        invoke $CONTRACT_NAME $FUNCTION_NAME "${FUNC_ARGS[@]}"
        ;;
    query)
        query $CONTRACT_NAME $FUNCTION_NAME "${FUNC_ARGS[@]}"
        ;;
    * )
        printHelp
        exit 1
        ;;
esac