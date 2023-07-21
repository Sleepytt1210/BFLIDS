from data.loader import load_data
import flwr as fl
import utils.config as cfg
import os
import models.net as net
from strategy.BFedAvg import BFedAvg
from client import BFLClient

SAVE_DIR = os.path.abspath('./model_ckpt_test/') if cfg.WORK_ENV == 'TEST' else os.path.abspath('./model_ckpt/')
DATA_ROOT = os.path.abspath('./data/datasets')

def client_fn(cid: str):
    x_train, x_test, y_train, y_test = load_data(DATA_ROOT, cfg.NUM_CLIENTS, cid)
    model = net.get_simple_model() if cfg.WORK_ENV == 'TEST' else net.get_model()

    # Start client
    print(f"Client connecting to server {cfg.S_ADDR}")
    client = BFLClient(cid, model, x_train, y_train, x_test, y_test)
    return client

strategy = BFedAvg(
    save_path=SAVE_DIR,
    min_fit_clients=cfg.NUM_CLIENTS,
    min_evaluate_clients=cfg.NUM_CLIENTS,
    min_available_clients=cfg.NUM_CLIENTS
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
