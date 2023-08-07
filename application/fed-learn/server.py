from data.loader import load_data
from utils.saver import hash_params, save_params
import os
import models.net as net
from strategy.BFedAvg import BFedAvg

from history import BFedHistory
from client import BFLClient
from bflcm import BFLClientManager

import flwr as fl
from flwr.server import Server
from flwr.server.client_proxy import ClientProxy
from flwr.common import GetParametersIns, ndarrays_to_parameters, parameters_to_ndarrays
from flwr.common.logger import log
from flwr.common.typing import Metrics, Parameters
import ipfshttpclient2 as ipfshttpclient

import utils.config as cfg
from utils.requestor import post_model, query_model, response_handler

from typing import List, Tuple

from logging import INFO, ERROR
import timeit


SAVE_DIR = os.path.abspath('./model_ckpt/tmp/') if cfg.WORK_ENV == 'TEST' else os.path.abspath('./model_ckpt/')
DATA_ROOT = os.path.abspath('./data/datasets')
CHANNEL_NAME="fedlearn"
CHAINCODE_NAME="checkpoints"
CONTRACT_NAME="GlobalLearningContract"
ALGORITHM="BiLSTM"

class BFLServer(Server):
    def __init__(self, associated_client_id: str, algorithm_name: str, temp_model_file_path: str = SAVE_DIR, **kwargs):
        Server.__init__(self, **kwargs)
        self.associated_client_id: str = associated_client_id
        self.algorithm = algorithm_name
        self.ipfs_client = None
        self.temp_model_file_path = temp_model_file_path
        self.model = net.get_model()
        self.associated_client: ClientProxy = None
        self.fed_session = 0

    def fit(self, num_rounds: int, timeout: float | None) -> BFedHistory:
        """Run federated averaging for a number of rounds."""

        # Assume the same env vars has been set by the user for both server and client script
        associated_client_config = cfg.get_env_for_client(self.associated_client_id)
        log(INFO, f"Waiting for associated client's connection!")

        self.associated_client = self.client_manager().get_client(self.associated_client_id, 300)

        if self.associated_client == None:
            log(ERROR, f"Timeout waiting for associated client's connection!")
            exit(1)

        ipfs_client = ipfshttpclient.Client(f"/ip4/{associated_client_config['IPFS_HOST']}/tcp/{int(associated_client_config['IPFS_API_PORT'])}/http")

        # Get the latest checkpoint from the global checkpoint ledger
        client_name = "User1@" + associated_client_config["PEER_DOMAIN"]
        latest_cps = query_model(f"{cfg.CHECKPOINTS_QUERY_URL}latestcheckpoint", CHANNEL_NAME, CHAINCODE_NAME, CONTRACT_NAME, client_name)
        self.latest_checkpoint = latest_cps if len(latest_cps) > 0 else None
        history = BFedHistory()

        self.fed_session = self.latest_checkpoint["FedSession"] + 1 if self.latest_checkpoint != None else 1
        self.strategy.set_fed_session(self.fed_session)

        # Initialize parameters
        log(INFO, "Initializing global parameters")
        self.parameters = self._get_initial_parameters(timeout, ipfs_client)
        log(INFO, f"Waiting for enough cients to join ({self.strategy.min_available_clients})")

        self.client_manager().wait_for(self.strategy.min_available_clients)
        log(INFO, "FL starting")
        start_time = timeit.default_timer()

        for current_round in range(1, num_rounds + 1):
            # Train model and replace previous global model
            res_fit = self.fit_round(
                server_round=current_round,
                timeout=timeout,
            )
            if res_fit is not None:
                parameters_prime, _, _ = res_fit  # fit_metrics_aggregated
                if parameters_prime:
                    self.parameters = parameters_prime

            # Evaluate model on a sample of available clients
            res_fed = self.evaluate_round(server_round=current_round, timeout=timeout)
            if res_fed is not None:
                loss_fed, evaluate_metrics_fed, _ = res_fed
                if loss_fed is not None:
                    history.add_loss_distributed(
                        server_round=current_round, loss=loss_fed
                    )
                    history.add_metrics_distributed(
                        server_round=current_round, metrics=evaluate_metrics_fed
                    )
            
                    # Post global model to blockchain
                    self.model.set_weights(parameters_to_ndarrays(self.parameters))
                    prefix = f"gmodel_fs{self.fed_session}_r{current_round}"
                    file_name = f"{prefix}.keras"
                    cid = save_params(os.path.join(self.temp_model_file_path, file_name), ipfs_client, self.model)
                    self._post_global_round_model(current_round, self.parameters, f"/ipfs/{cid}", prefix, client_name, loss_fed, evaluate_metrics_fed["accuracy"])

        # Round finished, clear parameters from memory
        self.parameters = None

        # Close the client after use
        ipfs_client.close()

        # Bookkeeping
        end_time = timeit.default_timer()
        elapsed = end_time - start_time
        log(INFO, "FL finished in %s", elapsed)
        return history
    
    def _get_initial_parameters(self, timeout: float | None, ipfs_client: ipfshttpclient.Client) -> Parameters:
        """Get initial parameters from one of the available clients."""

        if self.latest_checkpoint and self.ipfs_client:
            with open(self.temp_model_file_path, 'wb+') as f:
                f.write(ipfs_client.cat(self.latest_checkpoint["URL"]))
                f.flush()
                f.close()
                self.model.load_weights(self.temp_model_file_path)
                return ndarrays_to_parameters(self.model.get_weights())

        # Server-side parameter initialization
        parameters: Parameters | None = self.strategy.initialize_parameters(
            client_manager=self._client_manager,
        )
        if parameters is not None:
            log(INFO, "Using initial parameters provided by strategy")
            return parameters

        # Get initial parameters from one of the clients
        log(INFO, "Requesting initial parameters from the associated client")
        ins = GetParametersIns(config={})
        get_parameters_res = self.associated_client.get_parameters(ins=ins, timeout=timeout)
        log(INFO, "Received initial parameters from the associated client")
        return get_parameters_res.parameters


    def _post_global_round_model(
            self, server_round: int, parameters: Parameters, ipfs_url: str, model_prefix: str, client_name: str, accuracy: float, loss: float
    ) -> str:
        """Post a global model to the hyperledger fabric ledger via a smart contract"""
        hash = hash_params(parameters)
        model_id = f"{model_prefix}_{hash}"
        resp = post_model(req_url=f"{cfg.CHECKPOINTS_INVOKE_URL}create",
                   id=model_id,
                   hash=hash,
                   url=ipfs_url,
                   owner=client_name,
                   accuracy=accuracy,
                   algorithm=self.algorithm,
                   loss=loss,
                   round=server_round,
                   fed_session=self.fed_session,
                   channel_name=CHANNEL_NAME,
                   chaincode_name=CHAINCODE_NAME,
                   contract_name=CONTRACT_NAME,
                   client=client_name
        )

        log(INFO, str(resp))

def client_fn(cid: str):
    x_train, x_test, y_train, y_test = load_data(DATA_ROOT, cfg.NUM_CLIENTS, cid)
    model = net.get_model() if cfg.WORK_ENV == 'TEST' else net.get_model()

    # Start client
    print(f"Client connecting to server {cfg.S_ADDR}")
    client = BFLClient(cid, model, x_train, y_train, x_test, y_test)
    return client

def fit_config_fn(server_round: int, fed_session: int):
    config = {
        'server_round': server_round,
        'fed_session': fed_session
    }
    return config

def eval_metrics_aggregation_fn(results: List[Tuple[int, Metrics]]):
    # Weigh accuracy of each client by number of examples used
    accuracies = [metric["accuracy"] * num for num, metric in results]
    examples = [num for num, _ in results]

    # Aggregate and print custom metric
    aggregated_accuracy = sum(accuracies) / sum(examples)
    return {"accuracy": aggregated_accuracy}

strategy = BFedAvg(
    save_path=SAVE_DIR,
    min_fit_clients=cfg.NUM_CLIENTS,
    min_evaluate_clients=cfg.NUM_CLIENTS,
    min_available_clients=cfg.NUM_CLIENTS,
    on_fit_config_fn=fit_config_fn,
    evaluate_metrics_aggregation_fn=eval_metrics_aggregation_fn
)

if __name__ == "__main__":
    print(f"Starting server at {cfg.S_ADDR}")
    if cfg.WORK_ENV == "TEST" or cfg.WORK_ENV == "SIM":
        fl.simulation.start_simulation(
            client_fn = client_fn,
            clients_ids= [str(i) for i in range(1, cfg.NUM_CLIENTS + 1)],
            strategy = strategy,
            server=BFLServer('1', "BiLSTM", strategy=strategy, client_manager=BFLClientManager()),
            num_clients = cfg.NUM_CLIENTS,
            config = fl.server.ServerConfig(num_rounds=cfg.NUM_ROUNDS),
            client_resources=None,
        )
    elif cfg.WORK_ENV == "PROD":
        fl.server.start_server(
            server_address=cfg.S_ADDR,
            server=BFLServer('1', "BiLSTM", strategy=strategy, client_manager=BFLClientManager()),
            strategy=strategy, 
            config=fl.server.ServerConfig(num_rounds=cfg.NUM_ROUNDS),
        )
    else:
        print(f"Invalid working value ${cfg.WORK_ENV}!")
        exit(1)
