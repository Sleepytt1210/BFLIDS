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

CHECKPOINTS_REQ_URL=f"http://{EXPRESS_HOST}:{EXPRESS_PORT}/transactions/checkpoint/" 

"""Client ENV_VARS"""

CLIENT_ENV = dict()

if os.environ['RUNNING'] == 'CLIENT':
    CID = env_def('CLIENT_ID', '1')
    client_name = 'Org' + CID 
    peer_domain = client_name.lower() + '.example.com'
    CLIENT_ENV["ORG"] = env_def("ORG", client_name)
    CLIENT_ENV["MSP_ID"] = env_def("MSP_ID", client_name + "MSP")
    crypto_path = os.path.join(os.curdir, '..', '..', 'network', 'organizations', 'peerOrganizations', peer_domain)
    CLIENT_ENV["KEY_DIRECTORY_PATH"] = env_def("KEY_DIRECTORY_PATH", os.path.join(crypto_path, 'users', f'User1@{peer_domain}', 'msp', 'keystore')) 
    CLIENT_ENV["CERT_PATH"] = env_def("CERT_PATH", os.path.join(crypto_path, 'users', f'User1@{peer_domain}', 'msp', 'signcerts', 'cert.pem'))
    CLIENT_ENV["TLS_CERT_PATH"] = env_def("TLS_CERT_PATH", os.path.join(crypto_path, 'peers', f'peer0.{peer_domain}', 'tls', 'ca.crt'))
    CLIENT_ENV["PEER_HOST_ALIAS"] = env_def("PEER_HOST_ALIAS", peer_domain)
    CLIENT_ENV["HOST"] = env_def("C_HOST", "0.0.0.0")
    CLIENT_ENV["PORT"] = env_def("C_PORT", str(7051 + (1000 * (int(CID) - 1))))
    CLIENT_ENV["EXPRESS_HOST"] = env_def("EXPRESS_HOST", "0.0.0.0")
    CLIENT_ENV["EXPRESS_PORT"] = env_def("EXPRESS_PORT", 30027 + int(CID) - 1)

    CLIENT_ENV["IPFS_PATH"] = env_def("IPFS_PATH", os.path.join(os.curdir, '..', '..', 'ipfs-conf', peer_domain))
    offset = 1000 * (int(CID) - 1)

    CLIENT_ENV["IPFS_HOST"] = env_def("IPFS_HOST", "0.0.0.0")
    CLIENT_ENV["IPFS_GATEWAY_PORT"] = env_def("IPFS_GATEWAY_PORT", str(9898 + offset))
    CLIENT_ENV["IPFS_API_PORT"] = env_def("IPFS_API_PORT", str(5001 + offset))
    CLIENT_ENV["IPFS_SWARM_PORT"] = env_def("IPFS_SWARM_PORT", str(4001 + (int(CID) - 1)))
    CLIENT_ENV["IPFS_SWARM_TARGET"] = os.environ['IPFS_SWARM_TARGET']