from history import BFedHistory
from data.loader import load_data
from utils.saver import save_params
import os
import models.net as net
from strategy.BFedAvg import BFedAvg
from client import BFLClient

import flwr as fl
from flwr.server import Server
from flwr.server.client_proxy import ClientProxy
from flwr.common import GetPropertiesIns, GetParametersIns, ndarrays_to_parameters
from flwr.common.logger import log
from flwr.common.typing import Metrics, Parameters

import utils.config as cfg
from typing import List, Tuple

from logging import INFO
import timeit


SAVE_DIR = os.path.abspath('./model_ckpt/tmp/') if cfg.WORK_ENV == 'TEST' else os.path.abspath('./model_ckpt/')
DATA_ROOT = os.path.abspath('./data/datasets')

class BFLServer(Server):
    def __init__(self, associated_client_id: str, algorithm_name: str, temp_model_file_path: str = SAVE_DIR):
        super.__init__()
        self.associated_client_id: str = associated_client_id
        self.algorithm = algorithm_name
        self.ipfs_client = None
        self.temp_model_file_path = temp_model_file_path
        self.model = net.get_model()

    def fit(self, num_rounds: int, timeout: float | None) -> BFedHistory:
        """Run federated averaging for a number of rounds."""
        associated_client = self.client_manager().all()[self.associated_client_id]
        
        properties_ins = GetPropertiesIns({})
        properties_res = associated_client.get_properties(ins=properties_ins, timeout=timeout)
        props = properties_res.properties
        self.ipfs_client = props["ipfs_client"]

        history = BFedHistory(props["domain_name"], self.algorithm)
        fed_session = history.current_fed_session
        self.strategy.set_fed_session(fed_session)

        self.previous_latest = history.latest_checkpoint

        # Initialize parameters
        log(INFO, "Initializing global parameters")
        self.parameters = self._get_initial_parameters(timeout=timeout)
        
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
            self.model.set_weights(fl.common.parameters_to_ndarrays(self.parameters))
            file_name = f"gmodel_rc{history.current_fed_session}_r{current_round}.keras"
            cid = save_params(os.path.join(self.temp_model_file_path, file_name), self.ipfs_client, self.model)
            
            history.post_global_round_model(current_round, self.parameters, f"/ipfs/{cid}")
        
            # Round finished, clear parameters from memory
            self.parameters = None

        # Bookkeeping
        end_time = timeit.default_timer()
        elapsed = end_time - start_time
        log(INFO, "FL finished in %s", elapsed)
        return history
    
    def _get_initial_parameters(self, timeout: float | None, associated_client: ClientProxy) -> Parameters:
        """Get initial parameters from one of the available clients."""

        if self.previous_latest and self.previous_latest["URL"] and self.ipfs_client:
                with open(self.temp_model_file_path, 'wb+') as f:
                    f.write(self.ipfs_client.cat(self.previous_latest["URL"]))
                    f.flush()
                    f.close()
                    self.model.load_weights(self.temp_model_file_path)
                    return self.model.get_weights()

        # Server-side parameter initialization
        parameters: Parameters | None = self.strategy.initialize_parameters(
            client_manager=self._client_manager,
        )
        if parameters is not None:
            log(INFO, "Using initial parameters provided by strategy")
            return parameters

        # Get initial parameters from one of the clients
        log(INFO, "Requesting initial parameters from one random client")
        associated_client = self.client_manager().all()[self.associated_client_id]
        ins = GetParametersIns(config={})
        get_parameters_res = associated_client.get_parameters(ins=ins, timeout=timeout)
        log(INFO, "Received initial parameters from one random client")
        return get_parameters_res.parameters



def client_fn(cid: str):
    x_train, x_test, y_train, y_test = load_data(DATA_ROOT, cfg.NUM_CLIENTS, cid)
    model = net.get_simple_model() if cfg.WORK_ENV == 'TEST' else net.get_model()

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
    if cfg.WORK_ENV == "TEST":
        fl.simulation.start_simulation(
            client_fn = client_fn,
            strategy = strategy,
            server=BFLServer('1', "BiLSTM"),
            num_clients = cfg.NUM_CLIENTS,
            config = fl.server.ServerConfig(num_rounds=cfg.NUM_ROUNDS),
            client_resources=None,
        )
    elif cfg.WORK_ENV == "PROD":
        fl.server.start_server(
            server_address=cfg.S_ADDR,
            server=BFLServer('1', "BiLSTM"),
            strategy=strategy, 
            config=fl.server.ServerConfig(num_rounds=cfg.NUM_ROUNDS),
        )
    else:
        print(f"Invalid working value ${cfg.WORK_ENV}!")
        exit(1)
