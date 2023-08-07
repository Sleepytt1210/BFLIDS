import os
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv('.env')
found = load_dotenv(dotenv_path)

if not found:
    print("Dotenv file cannot be found or loaded!")
    exit(1)


def env_def(key: str, default: str):
    """Get environment value by key or return the default value

    Args:
        key (str): Environment variable key
        default (str): Default value

    Returns:
        str: Environment variable value
    """
    return os.environ.get(key, default) or default

"""Server ENV_VARS"""

WORK_ENV = env_def('WORK_ENV', 'TEST')
S_HOST = os.environ['FL_S_HOST']
S_PORT = os.environ['FL_S_PORT']
S_ADDR = f'{S_HOST}:{S_PORT}'

NUM_CLIENTS = int(os.environ['NUM_CLIENTS'])
NUM_ROUNDS = int(env_def('NUM_ROUNDS', 1))

EXPRESS_HOST = env_def("EXPRESS_HOST", "0.0.0.0")
EXPRESS_PORT = env_def("EXPRESS_PORT", 30027)

CHECKPOINTS_INVOKE_URL=f"http://{EXPRESS_HOST}:{EXPRESS_PORT}/transactions/checkpoint/" 
CHECKPOINTS_QUERY_URL=f"http://{EXPRESS_HOST}:{EXPRESS_PORT}/query/checkpoint/" 

"""Client ENV_VARS"""

def get_env_for_client(cid: str):
    
    client_env = os.environ.copy()
    client_name = 'Org' + cid 
    peer_domain = f"{client_name.lower()}.example.com"
    client_env["ORG"] = env_def("ORG", client_name)
    client_env["PEER_DOMAIN"] = peer_domain
    client_env["MSP_ID"] = env_def("MSP_ID", client_name + "MSP")
    crypto_path = os.path.join(os.curdir, '..', '..', 'network', 'organizations', 'peerOrganizations', peer_domain)
    client_env["KEY_DIRECTORY_PATH"] = env_def("KEY_DIRECTORY_PATH", os.path.join(crypto_path, 'users', f'User1@{peer_domain}', 'msp', 'keystore')) 
    client_env["CERT_PATH"] = env_def("CERT_PATH", os.path.join(crypto_path, 'users', f'User1@{peer_domain}', 'msp', 'signcerts', 'cert.pem'))
    client_env["TLS_CERT_PATH"] = env_def("TLS_CERT_PATH", os.path.join(crypto_path, 'peers', f'peer0.{peer_domain}', 'tls', 'ca.crt'))
    client_env["PEER_HOST_ALIAS"] = env_def("PEER_HOST_ALIAS", "peer0." + peer_domain)
    client_env["HOST"] = env_def("C_HOST", "0.0.0.0")
    client_env["PORT"] = env_def("C_PORT", 7051 + (1000 * (int(cid) - 1)))
    client_env["EXPRESS_HOST"] = env_def("EXPRESS_HOST", "0.0.0.0")
    client_env["EXPRESS_PORT"] = env_def("EXPRESS_PORT", 30027)
    
    client_env["TEMP_SAVE_PATH"] = env_def("TEMP_SAVE_PATH", os.path.abspath('model_ckpt/tmp'))

    client_env["IPFS_PATH"] = env_def("IPFS_PATH", os.path.join(os.curdir, '..', '..', 'ipfs-conf', peer_domain))
    offset = 1000 * (int(cid) - 1)

    client_env["IPFS_HOST"] = env_def("IPFS_HOST", "0.0.0.0")
    client_env["IPFS_GATEWAY_PORT"] = env_def("IPFS_GATEWAY_PORT", 9898 + offset)
    client_env["IPFS_API_PORT"] = env_def("IPFS_API_PORT",5001 + offset)
    client_env["IPFS_SWARM_PORT"] = env_def("IPFS_SWARM_PORT", 4001 + (int(cid) - 1))
    client_env["IPFS_SWARM_TARGET"] = os.environ['IPFS_SWARM_TARGET']

    # Parse all values to string
    for k, v in client_env.items():
        if type(v) == 'str':
            continue
        client_env[k] = str(v)

    return client_env