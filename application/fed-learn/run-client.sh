export RUNNING='CLIENT'
export CLIENT_ID=$1

echo "Starting Client $CLIENT_ID"
export C_HOST='0.0.0.0'

case "$CLIENT_ID" in
    1 ) 
        PORT='7051'
        ;;
    2 )
        PORT='9051'
        ;;
    3 )
        PORT='11051'
        ;;
esac

if [[ "$CLIENT_ID" == '1' ]]; then
    export RUNNING_SERVER=true
fi

export C_PORT="$PORT"

python client.py