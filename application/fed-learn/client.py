import flwr as fl
import tensorflow as tf
import models.net as net
from data.loader import load_data
from utils.config import NUM_CLIENTS, CID, S_ADDR
from subprocess import Popen
import os
import os.path as path
import utils.config as cfg
import ipfsApi
import time

class BFLClient(fl.client.NumPyClient):

    def __init__(self, cid: int, model: tf.keras.Model, x_train, y_train, x_test, y_test) -> None:
        self.model = model
        self.cid = cid
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test
        
        self.gateway_ps: Popen = None
        self.ipfs_daemon: Popen = None
        self.ipfs_connection: Popen = None
        self.ipfs_id = None
        self.__setup()

    def get_parameters(self, config):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        with tf.device('/device:gpu:0'):
            self.model.fit(self.x_train, self.y_train, epochs=1, batch_size=32)
        return self.model.get_weights(), len(self.x_train), {}

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        loss, accuracy = self.model.evaluate(self.x_test, self.y_test)
        return loss, len(self.x_test), {"accuracy": float(accuracy)}
    
    def terminate(self):
        if self.gateway_ps:
            self.gateway_ps.terminate()
            self.gateway_ps = None
        if self.ipfs_daemon:
            self.ipfs_daemon.terminate()
            self.ipfs_daemon = None
        if self.ipfs_connection:
            self.ipfs_connection.terminate()
            self.ipfs_connection = None

    def __setup(self):
        self.terminate()

        env_vars = self.__setup_env()

        print(f"[CLIENT {self.cid}]: Starting blockchain gateway")
        self.gateway_ps = Popen(
            ['npm', 'run', 'start'], 
            env=env_vars,
            cwd=os.path.join(os.curdir, '..', 'agent')
        )

        time.sleep(5)

        print(f"[CLIENT {self.cid}]: Starting IPFS daemon")
        self.ipfs_daemon = Popen(
            ['ipfs.sh', 'setup'],
            env=env_vars,
        )

        api = ipfsApi.Client(env_vars['IPFS_HOST'], env_vars["IPFS_API_PORT"])
        self.ipfs_id = api.id()
        
        s_target = env_vars["IPFS_SWARM_TARGET"]
        if self.ipfs_id['Addresses'][0] != s_target:
            print(f"[CLIENT {self.cid}]: Connecting to {s_target}")
            api.swarm_connect(env_vars["IPFS_SWARM_TARGET"])

    def __setup_env(self):
        
        cid = str(self.client.cid)
        client_name = 'Org' + cid 
        peer_domain = client_name.lower() + '.example.com'
        env_vars = dict()
        env_vars["ORG"] = os.environ.get("ORG", client_name)
        env_vars["MSP_ID"] = os.environ.get("MSP_ID", client_name + "MSP")
        crypto_path = os.path.join(os.curdir, '..', '..', 'network', 'organizations', 'peerOrganizations', peer_domain)
        env_vars["KEY_DIRECTORY_PATH"] = os.environ.get("KEY_DIRECTORY_PATH", os.path.join(crypto_path, 'users', f'User1@{peer_domain}', 'msp', 'keystore')) 
        env_vars["CERT_PATH"] = os.environ.get("CERT_PATH", os.path.join(crypto_path, 'users', f'User1@{peer_domain}', 'msp', 'signcerts', 'cert.pem'))
        env_vars["TLS_CERT_PATH"] = os.environ.get("TLS_CERT_PATH", os.path.join(crypto_path, 'peers', f'peer0.{peer_domain}', 'tls', 'ca.crt'))
        env_vars["PEER_HOST_ALIAS"] = peer_domain
        env_vars["HOST"] = os.environ.get("C_HOST", "0.0.0.0")
        env_vars["PORT"] = os.environ.get("C_PORT")
        env_vars["EXPRESS_PORT"] = cfg.EXPRESS_PORT

        env_vars["IPFS_PATH"] = os.environ.get("IPFS_PATH", os.path.join(os.curdir, '..', '..', 'ipfs-conf', peer_domain))
        offset = 1000 * (int(cid) - 1)

        env_vars["IPFS_HOST"] = os.environ.get("IPFS_HOST", "0.0.0.0")
        env_vars["IPFS_GATEWAY_PORT"] = os.environ.get("IPFS_GATEWAY_PORT", 9898 + offset)
        env_vars["IPFS_API_PORT"] = os.environ.get("IPFS_API_PORT", 5001 + offset)
        env_vars["IPFS_SWARM_PORT"] = os.environ.get("IPFS_SWARM_PORT", 4001 + (int(cid) - 1))
        env_vars["IPFS_SWARM_TARGET"] = cfg.IPFS_SWARM_TARGET

        # Populate other env vars
        for k, v in os.environ.items:
            if env_vars.get(k) == None:
                env_vars = v

        return env_vars

DATA_ROOT = path.abspath("data/datasets/")

def main() -> None:
    """Load data, start CifarClient."""

    # Load model and data
    print("Number of clients:", NUM_CLIENTS)

    print("Loading model and data for client", CID)
    x_train, x_test, y_train, y_test = load_data(DATA_ROOT, NUM_CLIENTS, CID)
    model = net.get_model()

    # Start client
    print(f"Client connecting to server {S_ADDR}")
    client = BFLClient(CID, model, x_train, y_train, x_test, y_test)
    fl.client.start_numpy_client(server_address=S_ADDR, client=client)

if __name__ == "__main__":
    main()