"""Training history retrieved from the blockchain ledger."""

from functools import reduce
from typing import Dict, List, Tuple

from flwr.common.typing import Scalar
from flwr.server import History


class BFedHistory(History):
    """History class for training and/or evaluation metrics collection."""

    def __init__(self) -> None:
        self.losses_distributed: List[Tuple[int, float]] = []
        self.losses_centralized: List[Tuple[int, float]] = []
        self.metrics_distributed_fit: Dict[str, List[Tuple[int, Scalar]]] = {}
        self.metrics_distributed: Dict[str, List[Tuple[int, Scalar]]] = {}
        self.metrics_centralized: Dict[str, List[Tuple[int, Scalar]]] = {}

    def add_loss_distributed(self, server_round: int, loss: float) -> None:
        """Add one loss entry (from distributed evaluation).
           Data is in the form of (server_round, loss)
        Args:
            server_round (int): Current communication round
            loss (float): Aggregated loss
        """
        self.losses_distributed.append((server_round, loss))

    def add_metrics_distributed(
        self, server_round: int, metrics: Dict[str, Scalar]
    ) -> None:
        """Add metrics entries (from distributed evaluation).
           Each metric is in the form of {metric_key: (server_round, value)}

        Args:
            server_round (int): Current communication round
            metrics (Dict[str, Scalar]): Distributed metrics where key is the name of metric and value is its value
        """
        for key in metrics:
            # if not (isinstance(metrics[key], float) or isinstance(metrics[key], int)):
            #     continue  # ignore non-numeric key/value pairs
            if key not in self.metrics_distributed:
                self.metrics_distributed[key] = []
            self.metrics_distributed[key].append((server_round, metrics[key]))

    def __repr__(self) -> str:
        """Create a representation of History.

        The representation consists of the following data (for each round) if present:

        * distributed loss.
        * distributed evaluation metrics.

        Returns
        -------
        representation : str
            The string representation of the history object.
        """
        rep = "Fed Session: " + self.current_fed_session + "\n"
        if self.losses_distributed:
            rep += "History (loss, distributed):\n" + reduce(
                lambda a, b: a + b,
                [
                    f"\tround {server_round}: {loss}\n"
                    for server_round, loss in self.losses_distributed
                ],
            )
        if self.losses_centralized:
            rep += "History (loss, centralized):\n" + reduce(
                lambda a, b: a + b,
                [
                    f"\tround {server_round}: {loss}\n"
                    for server_round, loss in self.losses_centralized
                ],
            )
        if self.metrics_distributed_fit:
            rep += "History (metrics, distributed, fit):\n" + str(
                self.metrics_distributed_fit
            )
        if self.metrics_distributed:
            rep += "History (metrics, distributed, evaluate):\n" + str(
                self.metrics_distributed
            )
        if self.metrics_centralized:
            rep += "History (metrics, centralized):\n" + str(self.metrics_centralized)
        return rep