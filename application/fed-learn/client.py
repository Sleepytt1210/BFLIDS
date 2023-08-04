import flwr as fl
import tensorflow as tf
import models.net as net
from data.loader import load_data
from utils.config import NUM_CLIENTS, CID, S_ADDR, env_def
from subprocess import Popen
from utils.saver import hash_params, save_params
from utils.requestor import post_model, query_model

import os
import os.path as path
import ipfshttpclient2 as ipfshttpclient
import utils.config as cfg
import time


CHANNEL_NAME='fedlearn'
CHAINCODE_NAME=['checkpoints', 'accuracyT']
CONTRACT_NAME='LocalLearningContract'

client_ports = {
    '1': 7051,
    '2': 9051,
    '3': 11051
}

class BFLClient(fl.client.NumPyClient):

    def __init__(self, cid: int, model: tf.keras.Model, x_train, y_train, x_test, y_test, running_server: bool = False) -> None:
        self.model = model
        self.cid = cid
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test
        self.running_server = running_server
        
        self.gateway_ps: Popen = None
        self.ipfs_daemon: Popen = None
        self.ipfs_client: ipfshttpclient.client.Client = None
        self.__setup()

    def get_parameters(self, config):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        
        with tf.device('/device:gpu:0'):
            self.model.fit(self.x_train, self.y_train, epochs=5, batch_size=32)

        loss, accuracy, _, _ = self.model.evaluate(self.x_test, self.y_test)
        
        # Post local model to IPFS
        server_round = config["server_round"]
        print(f"[CLIENT {self.cid}]: Uploading model for server round {server_round}")
        params = self.model.get_weights()
        hash = hash_params(params)
        id = f"model_r{server_round}_{self.cid}_{hash}"

        ipfs_cid = save_params(params)
        resource_url = f"/ipfs/{ipfs_cid}"

        owner = self.env_vars['PEER_HOST_ALIAS']
        request_url = f"http://{self.env_vars['EXPRESS_HOST']}:{self.env_vars['EXPRESS_PORT']}/transactions/checkpoint/create"
        post_model(
            req_url=request_url,
            id=id,
            hash=hash,
            url=resource_url,
            owner=owner,
            round=server_round,
            algorithm="BiLSTM",
            loss=loss,
            accuracy=accuracy,
            channel_name=CHANNEL_NAME,
            chaincode_name=CHAINCODE_NAME,
            contract_name=CONTRACT_NAME,
            client=f"Client {self.cid}"
        )

        return parameters, len(self.x_train), {}

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        loss, accuracy, specificity, sensitivity = self.model.evaluate(self.x_test, self.y_test)

        return loss, len(self.x_test), {"accuracy": float(accuracy), "specificity": float(specificity), "sensitivity": float(sensitivity)}
    
    def terminate(self):
        if self.gateway_ps:
            self.gateway_ps.terminate()
            self.gateway_ps = None
        if self.ipfs_daemon:
            self.ipfs_daemon.terminate()
            self.ipfs_daemon = None

    def __setup(self):
        self.terminate()

        self.env_vars = self.__setup_env()

        if not self.running_server and cfg.WORK_ENV == 'PROD':
            print(f"[CLIENT {self.cid}]: Starting blockchain gateway")
            nodejsPath = os.path.abspath(os.path.join(os.getcwd(), '..', 'agent'))
            self.gateway_ps = Popen(
                ['npm', 'run', 'start'], 
                env=self.env_vars,
                cwd=nodejsPath
            )

            time.sleep(20)

        print(f"[CLIENT {self.cid}]: Starting IPFS daemon")
        self.ipfs_daemon = Popen(
            ['./ipfs.sh', 'setup'],
            env=self.env_vars,
        )

        time.sleep(3)

        self.ipfs_client = ipfshttpclient.Client(addr=f"/ip4/{self.env_vars['IPFS_HOST']}/tcp/{int(self.env_vars['IPFS_API_PORT'])}/http")
        ipfs_id = dict(self.ipfs_client.id())
        
        s_target = self.env_vars["IPFS_SWARM_TARGET"]
        if ipfs_id['Addresses'][0] != s_target:
            print(f"[CLIENT {self.cid}]: Connecting to {s_target}")
            self.ipfs_client.swarm.connect(s_target)

    def __setup_env(self):
        env_vars = cfg.CLIENT_ENV
        
        # Populate other env vars
        for k, v in os.environ.items():
            if env_vars.get(k) == None:
                env_vars[k] = v

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