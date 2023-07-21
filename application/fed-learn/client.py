import flwr as fl
import tensorflow as tf
import models.net as net
from data.loader import load_data
from utils.config import NUM_CLIENTS, CID, S_ADDR
from subprocess import Popen
from utils.saver import hash_params
from utils.requestor import post_model, query_model

import os
import os.path as path
import utils.config as cfg
import ipfsApi
import time


CHANNEL_NAME='fedlearn'
CHAINCODE_NAME='fedLearn'
CONTRACT_NAME='LocalLearningContract'

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
        self.ipfs_api: ipfsApi.Client = None
        self.__setup()

    def get_parameters(self, config):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        with tf.device('/device:gpu:0'):
            self.model.fit(self.x_train, self.y_train, epochs=1, batch_size=32)

        loss, x_test_count, accuracy_dict = self.evaluate(parameters, config)
        
        # Post local model to IPFS
        server_round = config["server_round"]
        print(f"[Client {self.cid}]: Uploading model for server round {server_round}")
        params = self.model.get_weights()
        hash = hash_params(params)
        id = f"model_r{server_round}_{self.cid}_{hash}"

        ipfs_cid = self.ipfs_api.add_pyobj(params)
        resource_url = f"http://{self.env_vars['IPFS_HOST']}:{self.env_vars['IPFS_GATEWAY_PORT']}/ipfs/{ipfs_cid}"

        owner = self.env_vars['PEER_HOST_ALIAS']
        post_model(
            id=id,
            hash=hash,
            url=resource_url,
            owner=owner,
            round=server_round,
            algorithm="BiLSTM",
            loss=loss,
            accuracy=accuracy_dict['accuracy'],
            channel_name=CHANNEL_NAME,
            chaincode_name=CHAINCODE_NAME,
            contract_name=CONTRACT_NAME,
            client=f"Client {self.cid}"
        )

        return params, len(self.x_train), {}

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

        self.env_vars = self.__setup_env()

        print(f"[CLIENT {self.cid}]: Starting blockchain gateway")
        self.gateway_ps = Popen(
            ['npm', 'run', 'start'], 
            env=self.env_vars,
            cwd=os.path.join(os.curdir, '..', 'agent')
        )

        time.sleep(5)

        print(f"[CLIENT {self.cid}]: Starting IPFS daemon")
        self.ipfs_daemon = Popen(
            ['ipfs.sh', 'setup'],
            env=self.env_vars,
        )

        self.ipfs_api = ipfsApi.Client(self.env_vars['IPFS_HOST'], self.env_vars["IPFS_API_PORT"])
        ipfs_id = self.ipfs_api.id()
        
        s_target = self.env_vars["IPFS_SWARM_TARGET"]
        if ipfs_id['Addresses'][0] != s_target:
            print(f"[CLIENT {self.cid}]: Connecting to {s_target}")
            self.ipfs_api.swarm_connect(self.env_vars["IPFS_SWARM_TARGET"])

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

    print("Loading model and data for Client", CID)
    x_train, x_test, y_train, y_test = load_data(DATA_ROOT, NUM_CLIENTS, CID)
    model = net.get_model()

    # Start client
    print(f"Client {CID} connecting to server {S_ADDR}")
    client = BFLClient(CID, model, x_train, y_train, x_test, y_test)
    fl.client.start_numpy_client(server_address=S_ADDR, client=client)

if __name__ == "__main__":
    main()