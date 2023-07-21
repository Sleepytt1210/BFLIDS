#!/bin/bash

function printHelp() {
    echo "`basename ${0}`:usage: [-e TEST | PROD]" 
}

option="${1}" 
case ${option} in 
   -e)  export WORK_ENV="${2}" 
        case "${WORK_ENV}" in
            TEST | PROD) echo "Set working environment to ${WORK_ENV}";;
            *) echo "Only value TEST or PROD are accepted!"
            exit 1
            ;;
        esac
      ;;
   *)  
        printHelp
        exit 1 # Command to come out of the program with status 1
        ;; 
esac 

echo "Starting server at $(dotenv -f '../.env' get FL_S_HOST):$(dotenv -f '../.env' get FL_S_PORT)"

# python server.py