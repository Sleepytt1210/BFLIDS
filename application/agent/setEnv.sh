CRYPTO_PATH=${PWD}/../../network/organizations/peerOrganizations/org1.example.com
export ORG="Org1"
export KEY_DIRECTORY_PATH=${CRYPTO_PATH}/users/User1@org1.example.com/msp/keystore 
export CERT_PATH=${CRYPTO_PATH}/users/User1@org1.example.com/msp/signcerts/cert.pem
export TLS_CERT_PATH=${CRYPTO_PATH}/peers/peer0.org1.example.com/tls/ca.crt
export PEER_HOST_ALIAS=peer0.org1.example.com
export HOST="127.0.0.1"
export PORT="7051"
export EXPRESS_PORT=`dotenv -f '../.env' get EXPRESS_PORT`