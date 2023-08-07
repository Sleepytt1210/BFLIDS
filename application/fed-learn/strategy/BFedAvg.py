from typing import List, Tuple 
from flwr.common import Parameters, FitIns
from flwr.server import ClientManager
from flwr.server.client_proxy import ClientProxy
from flwr.server.strategy import FedAvg

class BFedAvg(FedAvg):
    def __init__(self, *args, save_path, **kwargs):
        super().__init__(*args, **kwargs)
        self.save_path = save_path
        self.fed_session = 0

    def configure_fit(
        self, server_round: int, parameters: Parameters, client_manager: ClientManager
    ) -> List[Tuple[ClientProxy, FitIns]]:
        """Configure the next round of training."""
        config = {}
        if self.on_fit_config_fn is not None:
            # Custom fit config function provided
            config = self.on_fit_config_fn(server_round, self.get_fed_session())
        fit_ins = FitIns(parameters, config)

        # Sample clients
        sample_size, min_num_clients = self.num_fit_clients(
            client_manager.num_available()
        )
        clients = client_manager.sample(
            num_clients=sample_size, min_num_clients=min_num_clients
        )

        # Return client/config pairs
        return [(client, fit_ins) for client in clients]

    def set_fed_session(self, fed_session):
        self.fed_session = fed_session

    def get_fed_session(self) -> int:
        return self.fed_session

