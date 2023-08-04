import hashlib as hl
import ipfshttpclient2 as ipfshttpclient
from flwr.common.typing import Parameters
from flwr.common.parameter import ndarrays_to_parameters, ndarray_to_bytes
from keras import Sequential

def to_param_bytes(parameters) -> Parameters:
    parameters = ndarrays_to_parameters(parameters)
    return b''.join(parameters.tensors)

def hash_params(parameters):
    if isinstance(parameters, list):
        parameters = to_param_bytes(parameters)
    return hl.sha256(b''.join(parameters.tensors)).hexdigest()

def save_params(filepath: str, ipfs_client: ipfshttpclient.client.Client, model: Sequential) -> str:
    """Save a model parameters to ipfs and return corresponding CID hash value.

    Args:
        filepath (str): The filepath to save the aggregated parameters locally.
        ipfs_client (ipfshttpclient.client.Client): The ipfs client to perform ipfs operation on behalf of a participant.
        model (Sequential): The model with the aggregated parameters set as its weights.

    Returns:
        str: CID which is a hash of the parameter stored on the private IPFS. 
    """
    
    model.save_weights(filepath=filepath)   
    result_dict = ipfs_client.add(filepath) 
    return result_dict['Hash'] 