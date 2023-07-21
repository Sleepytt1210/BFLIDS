import requests
import json

baseUrl = f"http://localhost:{30027}/transactions"


def postModel(id, hash, url, owner, round, accuracy, hAccuracy, algorithm, loss, channel_name, chaincode_name, contract_name, client):
    
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
            "hAccuracy": hAccuracy,
        }
    }
    
    resp = requests.post(
        url=f"{baseUrl}/checkpoint/create", 
        headers={'content-type': 'application/json'}, 
        json=data
    )

    return resp.text

def queryModel(id, channelName, chaincodeName, contractName, client):
    try:
        resp = requests.get(
            url=f"{baseUrl}/checkpoint/query/{id}",
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