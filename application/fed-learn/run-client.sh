export CLIENT_ID=$1

echo "Starting Client $CLIENT_ID"
export C_HOST='0.0.0.0'

case "$CLIENTID" in
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

export C_PORT=$PORT

python client.py