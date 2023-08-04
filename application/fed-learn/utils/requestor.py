import requests

def post_model(req_url, id, hash, url, owner, algorithm, accuracy, loss, round, fed_session, channel_name, chaincode_name, contract_name, client):

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
            "cAccuracy": accuracy,
            "loss": loss,
            "round": round,
            "fedSession": fed_session,
        }
    }

    resp = requests.post(
        url=req_url,
        headers={'content-type': 'application/json'},
        json=data
    )

    return response_handler({"status_code": resp.status_code, "result": resp.json()}, fed_session)

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
        return response_handler({"status_code": resp.status_code, "result": resp.json()})
    except:
        return None
    
def error_handler(err, fed_session):
    msg: str = err[0]["message"]
    if "CP400" in msg:
        print(msg[msg.index("CP400"):])
        print(f"Federated learning session {fed_session} will now abort!")
        exit(400)

def response_handler(response, fed_session=None):
    if response["status_code"] < 200 or response["status_code"] > 210 :
        error_handler(response["result"]["details"], fed_session)
    return response["result"]["result"]


# if __name__ == '__main__':
#     # resp = post_model("http://localhost:30027/transactions/checkpoint/create", 
#     #            "model_fs2_r1_0059f56e5034c19183adecdb2cfa9541a72022937b10e4376610ede911f6243f",
#     #            "0059f56e5034c19183adecdb2cfa9541a72022937b10e4376610ede911f6243f", 
#     #            "/ipfs/Qmex9gWyogEeGaXFEZmLWKrM67EqnUry6zQAW6f85qaV35", 
#     #            "org1.example.com", 
#     #            "BiLSTM", 
#     #            "95.7", 
#     #            "0.0210", 
#     #            "1", 
#     #            "2",
#     #            "fedlearn",
#     #            "checkpoints",
#     #            "GlobalLearningContract",
#     #            "org1.example.com")
    
#     # resp = query_model("http://localhost:30027/query/checkpoint/model_fs1_r3_80f298f00b4dc58a9ce9b5d8a400c03eeeb2fe82ad19b3c393dc8cc1a27d8327", "fedlearn",
#     #            "checkpoints",
#     #            "GlobalLearningContract",
#     #            "org1.example.com")
    
#     # resp = query_model(f"http://localhost:30027/query/checkpoint/latest", "fedlearn", "checkpoints", "GlobalLearningContract", "org1.example.com")
#     # print(type(resp[0]["FedSession"]))
    
