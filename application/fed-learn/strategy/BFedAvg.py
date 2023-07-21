from typing import Dict, List, Tuple
import flwr as fl
from flwr.common import FitRes, Parameters, Scalar
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg
import utils.saver as sv

class BFedAvg(FedAvg):
    def __init__(self, *args, save_path, **kwargs):
        super().__init__(*args, **kwargs)
        self.save_path = save_path

    def aggregate_fit(self, server_round: int, results: List[Tuple[ClientProxy, FitRes]], failures: List[Tuple[ClientProxy, FitRes] | BaseException]) -> Tuple[Parameters | None, Dict[str, Scalar]]:
        aggregated_parameters, aggregated_metrics = super().aggregate_fit(server_round, results, failures)
        file_name = f"model_r{server_round}.ckpt"
        if aggregated_parameters is not None:
            print(f"Saving round {server_round} aggregated_parameters...")
            sv.save_model(aggregated_parameters, self.save_path, file_name)

        return aggregated_parameters, aggregated_metrics

