import requests

def post_model(req_url, id, hash, url, owner, round, accuracy, algorithm, loss, channel_name, chaincode_name, contract_name, client):
    
    data = {
        "channelName": channel_name,
        "chaincodeName": chaincode_name,
        "contractName": contract_name,
        "client": client,
        "checkpointData": {
            "id": id,
            "hash": hash,
            "url": url,
            "algorithm": algorithm,
            "owner": owner,
            "round": round,
            "cAccuracy": accuracy,
            "loss": loss,
        }
    }
    
    resp = requests.post(
        url=req_url, 
        headers={'content-type': 'application/json'}, 
        json=data
    )

    return resp.text

def query_model(req_url, channelName, chaincodeName, contractName, client):
    try:
        resp = requests.get(
            url=req_url,
            params={
                'chn': channelName,
                'ccn': chaincodeName,
                'ctn': contractName,
                'clID': client
            }
        )
        return resp.text
    except:
        return None