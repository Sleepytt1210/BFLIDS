from history import BFedHistory
from data.loader import load_data
from utils.saver import save_params
import os
import models.net as net
from strategy.BFedAvg import BFedAvg
from client import BFLClient

import flwr as fl
from flwr.server import Server
from flwr.common.logger import log
from flwr.common.typing import Metrics

import utils.config as cfg
from typing import List, Tuple

from logging import INFO
import timeit


SAVE_DIR = os.path.abspath('./model_ckpt_test/') if cfg.WORK_ENV == 'TEST' else os.path.abspath('./model_ckpt/')
DATA_ROOT = os.path.abspath('./data/datasets')

class BFLServer(Server):
    def __init__(self, associated_client: BFLClient):
        super.__init__()
        self.associated_client = associated_client

    def fit(self, num_rounds: int, timeout: float | None) -> BFedHistory:
        """Run federated averaging for a number of rounds."""
        history = BFedHistory()

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


            model = net.get_model()
            model.set_weights(self.parameters)
            file_name = f"gmodel_rc{history.current_fed_session}_r{current_round}.keras"
            cid = save_params(os.path.abspath(f"model_ckpt/{file_name}"), self.associated_client.ipfs_client, model)
            
            history.post_global_round_model(current_round, self.parameters, f"/ipfs/{cid}")

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

        # Bookkeeping
        end_time = timeit.default_timer()
        elapsed = end_time - start_time
        log(INFO, "FL finished in %s", elapsed)
        return history



def client_fn(cid: str):
    x_train, x_test, y_train, y_test = load_data(DATA_ROOT, cfg.NUM_CLIENTS, cid)
    model = net.get_simple_model() if cfg.WORK_ENV == 'TEST' else net.get_model()

    # Start client
    print(f"Client connecting to server {cfg.S_ADDR}")
    client = BFLClient(cid, model, x_train, y_train, x_test, y_test)
    return client

def fit_config_fn(server_round: int):
    config = {
        'server_round': server_round,
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
    if cfg.WORK_ENV == 'TEST':
        fl.simulation.start_simulation(
            client_fn = client_fn,
            strategy = strategy,
            num_clients = cfg.NUM_CLIENTS,
            config = fl.server.ServerConfig(num_rounds=cfg.NUM_ROUNDS),
            client_resources=None,
        )
    elif cfg.WORK_ENV == 'PROD':
        fl.server.start_server(
            server_address=cfg.S_ADDR,
            strategy=strategy, 
            config=fl.server.ServerConfig(num_rounds=cfg.NUM_ROUNDS),
        )
    else:
        print(f"Invalid working value ${cfg.WORK_ENV}!")
        exit(1)
