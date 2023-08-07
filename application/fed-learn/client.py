import flwr as fl
from flwr.common.typing import Config, Scalar
from typing import Dict

import tensorflow as tf
import models.net as net
from data.loader import load_data
from utils.config import NUM_CLIENTS, S_ADDR
from subprocess import Popen
from utils.saver import hash_params, save_params
from utils.requestor import post_model, is_node_running

import os
import os.path as path
import ipfshttpclient2 as ipfshttpclient
import utils.config as cfg
import time


CHANNEL_NAME='fedlearn'
CHAINCODE_NAME='checkpoints'
CONTRACT_NAME='LocalLearningContract'

client_ports = {
    '1': 7051,
    '2': 9051,
    '3': 11051
}

class Callback(tf.keras.callbacks.Callback):
    """Callback class to print progress every 10 steps"""
    SHOW_NUMBER = 200
    counter = 0
    epoch = 0

    def __init__(self, cid):
        self.cid = cid

    def on_epoch_begin(self, epoch, logs=None):
        self.epoch = epoch

    def on_train_batch_end(self, batch, logs=None):
        if self.counter == self.SHOW_NUMBER or self.epoch == 1:
            print(f"[Client {self.cid}] Epoch {self.epoch} - {batch} - loss: {logs['loss']} - accuracy: {logs['accuracy']}")
            if self.epoch > 1:
                self.counter = 0
        self.counter += 1


class BFLClient(fl.client.NumPyClient):

    def __init__(self, cid: str, model: tf.keras.Model, x_train, y_train, x_test, y_test) -> None:
        self.model = model
        self.cid = cid
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test
        
        self.env_vars = cfg.get_env_for_client(str(cid))
        self.peer_name = self.env_vars["PEER_HOST_ALIAS"]
        self._gateway_ps: Popen = None
        self._ipfs_daemon: Popen = None
        self._ipfs_client: ipfshttpclient.client.Client = None
        self._setup()

    def get_properties(self, config: Config) -> Dict[str, Scalar]:
        return {"cid": self.cid, "peer_name": self.peer_name}

    def get_parameters(self, config):
        return self.model.get_weights()

    def _log(self, message: str):
        print(f"[CLIENT {self.cid}]: ", message)

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        
        epoch = 5 if cfg.WORK_ENV == 'PROD' else 2 

        with tf.device('/device:gpu:0'):
            self.model.fit(self.x_train, self.y_train, epochs=epoch, batch_size=32, callbacks=[Callback(self.cid)], verbose=0)

        loss, accuracy, _, _ = self.model.evaluate(self.x_test, self.y_test, callbacks=[Callback(self.cid)], verbose=0)
        
        # Post local model to IPFS
        server_round = config["server_round"]
        fed_session = config["fed_session"]

        self._log(f"Uploading model for server round {server_round}")
        params = self.model.get_weights()
        hash = hash_params(params)
        id = f"model_fs{fed_session}_r{server_round}_c{self.cid}_{hash}"

        filename = f"{self.env_vars['TEMP_SAVE_PATH']}/{id}.keras"
        ipfs_cid = save_params(filename, self._ipfs_client, self.model)
        resource_url = f"/ipfs/{ipfs_cid}"

        peer_domain = self.env_vars["PEER_DOMAIN"]
        owner = "User1@" + peer_domain
        request_url = f"http://{self.env_vars['EXPRESS_HOST']}:{self.env_vars['EXPRESS_PORT']}/transactions/checkpoint/create"
        resp = post_model(
            req_url=request_url,
            id=id,
            hash=hash,
            url=resource_url,
            owner=owner,
            round=server_round,
            algorithm="BiLSTM",
            accuracy=accuracy,
            loss=loss,
            fed_session=fed_session,
            channel_name=CHANNEL_NAME,
            chaincode_name=CHAINCODE_NAME,
            contract_name=CONTRACT_NAME,
            client=owner
        )

        self._log(resp)

        return parameters, len(self.x_train), {}

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        loss, accuracy, specificity, sensitivity = self.model.evaluate(self.x_test, self.y_test, callbacks=[Callback(self.cid)], verbose=0)

        return loss, len(self.x_test), {"accuracy": float(accuracy), "specificity": float(specificity), "sensitivity": float(sensitivity)}
    
    def terminate(self):
        if self._gateway_ps:
            self._gateway_ps.terminate()
            self._gateway_ps = None
        if self._ipfs_daemon:
            self._ipfs_daemon.terminate()
            self._ipfs_daemon = None
        if self._ipfs_client:
            self._ipfs_client.close()
            self._ipfs_client = None

    def _setup(self):
        self.terminate()

        self._setup_nodejs()

        self._setup_ipfs()
    
    def _setup_nodejs(self):
        
        if not self._is_port_in_use(self.env_vars['EXPRESS_PORT']):

            self._log(f"Starting blockchain gateway")
            nodejsPath = os.path.abspath(os.path.join(os.getcwd(), '..', 'agent'))
            self._gateway_ps = Popen(
                ['npm', 'run', 'start'], 
                env=self.env_vars,
                cwd=nodejsPath
            )

            is_running_flag = False

            # Wait till express service is running
            while not is_running_flag:
                try:
                    is_running_flag = is_node_running(f"http://{self.env_vars['EXPRESS_HOST']}:{self.env_vars['EXPRESS_PORT']}/health")
                except:
                    time.sleep(5)

    def _is_port_in_use(self, port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', int(port))) == 0
        
    def _setup_ipfs(self):
        
        if not self._is_port_in_use(self.env_vars['IPFS_GATEWAY_PORT']):

            self._log(f"Starting IPFS daemon")
            self._ipfs_daemon = Popen(
                ['./ipfs.sh', 'setup'],
                env=self.env_vars,
            )

            time.sleep(5)

        self._ipfs_client = ipfshttpclient.Client(addr=f"/ip4/{self.env_vars['IPFS_HOST']}/tcp/{int(self.env_vars['IPFS_API_PORT'])}/http")
        ipfs_id = dict(self._ipfs_client.id())
        
        s_target = self.env_vars["IPFS_SWARM_TARGET"]
        if ipfs_id['Addresses'][0] != s_target:
            self._log(f"Connecting to {s_target}")
            self._ipfs_client.swarm.connect(s_target)
        
DATA_ROOT = path.abspath("data/datasets/")

def main() -> None:
    """Load data, start CifarClient."""

    CID = cfg.env_def("CLIENT_ID", "1")

    # Load model and data
    print("Number of clients:", NUM_CLIENTS)

    print("Loading model and data for Client", CID)
    x_train, x_test, y_train, y_test = load_data(DATA_ROOT, NUM_CLIENTS, CID)
    model = net.get_model()

    # Start client
    print(f"Initializing client {CID}")
    client = BFLClient(CID, model, x_train, y_train, x_test, y_test)
    fl.client.start_numpy_client(server_address=S_ADDR, client=client)

if __name__ == "__main__":
    main()