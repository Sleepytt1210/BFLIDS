import os
import pickle
import hashlib as hl
from flwr.common.typing import NDArrays
from flwr.common.parameter import ndarrays_to_parameters

def save_model(parameters, save_path: str, file_name: str):
    path = os.path.join(save_path, file_name)
    os.makedirs(save_path, exist_ok=True)
    with open(path, 'wb') as file:
        pickle.dump(parameters, file)

def load_model(path: str):
    try:
        with open(path, 'rb') as file:
            return pickle.load(file)
    except IOError:
        print(f"Error loading file at {path}")
        return None
    
def hash_params(parameters):
    if isinstance(parameters, NDArrays):
        parameters = ndarrays_to_parameters(parameters)
    return hl.sha256(b''.join(parameters.tensors)).hexdigest()