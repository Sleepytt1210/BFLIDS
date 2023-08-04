from typing import Dict, List, Optional, Tuple, Union
import flwr as fl
from flwr.common import EvaluateRes, FitRes, Parameters, Scalar
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg
import utils.saver as sv
from utils.requestor import query_model

class BFedAvg(FedAvg):
    def __init__(self, *args, save_path, **kwargs):
        super().__init__(*args, **kwargs)
        self.save_path = save_path
        self.current_parameters = self.initial_parameters

