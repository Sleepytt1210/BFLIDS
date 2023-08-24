# """Training history retrieved from the blockchain ledger."""
from typing import Dict, List, Tuple

from flwr.common.typing import Scalar
from flwr.server import History

class BFLHistory(History):
    """History class for training and/or evaluation metrics collection."""

    def __init__(self) -> None:
        self.losses_distributed: List[Tuple[int, float]] = []
        self.losses_centralized: List[Tuple[int, float]] = []
        self.metrics_distributed_fit: Dict[str, List[Tuple[int, Scalar]]] = {}
        self.metrics_distributed: Dict[str, List[Tuple[int, Scalar]]] = {}
        self.metrics_centralized: Dict[str, List[Tuple[int, Scalar]]] = {}
        self.elapsed: float = 0

    def set_elapsed(self, elapsed):
        self.elapsed = elapsed