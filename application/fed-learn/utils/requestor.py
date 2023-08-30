import requests
import math

def post_model(req_url: str, id: str, hash: str, url: str, algorithm: str, accuracy: float, loss: float, fed_round: int, fed_session: int, channel_name: str, chaincode_name: str, contract_name: str, client: str):
    
    data = {
        "channelName": channel_name,
        "chaincodeName": chaincode_name,
        "contractName": contract_name,
        "clientName": client,
        "checkpointData": {
            "id": id,
            "hash": hash,
            "url": url,
            "algorithm": algorithm,
            "cAccuracy": round(accuracy, 6) * 100,
            "loss": round(loss, 6),
            "round": fed_round,
            "fedSession": fed_session,
        },
    }

    print(f"Posting model: {data}")

    resp = requests.post(
        url=req_url,
        headers={'content-type': 'application/json'},
        json=data
    )

    return response_handler(dict(status_code=resp.status_code, content=resp.json()), fed_session)

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
        return response_handler({"status_code": resp.status_code, "content": resp.json()})
    except:
        return []
    
def error_handler(err, fed_session=None):
    """HTTP error handler function. Used to handle error messages received from the API Server.

    Args:
        err (status: {
                    code: int,
                    message: str
                },
                reason: str,
                details: json || 'none',
                timestamp: str
            ): The error content returned by the API server in json format.
        fed_session (int): Currently running fed_session. Defaults to None.
    """
    msg: str = err["details"]
    print(err["reason"])
    if err["status"]["code"] == 404:
        print("The requested URL does not exist!")
    if "CP400" in msg:
        print(msg[msg.index("CP400"):])
        print(f"Federated learning session {fed_session} will now abort!")
        
    exit(1)

def is_node_running(req_url):
    return (requests.get(req_url)).status_code == requests.codes.ok

def response_handler(response, fed_session=None):
    """Handle response sent from NodeJS gateway

    Args:
        response ({status_code: int, content: json}): The http status code of the response and the full content sent back by the API Server.  
        fed_session (int, optional): The current federated learning session number for model creation. Defaults to None.

    Returns:
        Result (json): The JSON data which could be the queried item or any http response messages. 
    """
    print(str(response))
    if response["status_code"] < 200 or response["status_code"] > 210 :
        error_handler(response["content"], fed_session)
    return response["content"]["result"]


if __name__ == '__main__':
    # resp = post_model("http://localhost:30027/transactions/checkpoint/create", 
    #            "model_fs2_r1_0059f56e5034c19183adecdb2cfa9541a72022937b10e4376610ede911f6243f",
    #            "0059f56e5034c19183adecdb2cfa9541a72022937b10e4376610ede911f6243f", 
    #            "/ipfs/Qmex9gWyogEeGaXFEZmLWKrM67EqnUry6zQAW6f85qaV35", 
    #            "User1@org1.example.com", 
    #            "BiLSTM", 
    #            "95.7", 
    #            "0.0210", 
    #            "1", 
    #            "2",
    #            "fedlearn",
    #            "checkpoints",
    #            "GlobalLearningContract",
    #            "User1@org1.example.com")
    CHANNEL_NAME="fedlearn"
    CHAINCODE_NAME="checkpoints"
    CONTRACT_NAME="GlobalLearningContract"
    resp = query_model(f"http://localhost:30027/query/checkpoint/latestcheckpoint", CHANNEL_NAME, CHAINCODE_NAME, CONTRACT_NAME, "User1@org1.example.com")
    # resp = query_model("http://localhost:30027/query/checkpoint/latest", "fedlearn",
    #            "checkpoints",
    #            "GlobalLearningContract",
    #            "User1@org1.example.com")
    
    print(resp["URL"])
    
#     # resp = query_model(f"http://localhost:30027/query/checkpoint/latest", "fedlearn", "checkpoints", "GlobalLearningContract", "org1.example.com")
#     # print(type(resp[0]["FedSession"]))
    
