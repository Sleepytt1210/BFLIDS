"""Training history retrieved from the blockchain ledger."""

from functools import reduce
from typing import Dict, List, Tuple

from flwr.common.typing import Scalar, Parameters
from utils.requestor import post_model, query_model, response_handler
from utils.config import EXPRESS_HOST, EXPRESS_PORT
import json
from utils.saver import hash_params

GLOBAL_CHECKPOINTS_REQ_URL=f"http://{EXPRESS_HOST}:{EXPRESS_PORT}/transactions/checkpoint/" 

CHANNEL_NAME="fedlearn"
CHAINCODE_NAME="checkpoints"
CONTRACT_NAME="GlobalLearningContract"
ALGORITHM="BiLSTM"

class BFedHistory:
    """History class for training and/or evaluation metrics collection."""

    def __init__(self, client_name, algorithm) -> None:
        self.client_name = client_name
        result = query_model(f"{GLOBAL_CHECKPOINTS_REQ_URL}query/all", CHANNEL_NAME, CHAINCODE_NAME, CONTRACT_NAME, client_name)
        latest_checkpoint = query_model(f"{GLOBAL_CHECKPOINTS_REQ_URL}query/latestcheckpoint", CHANNEL_NAME, CHAINCODE_NAME, CONTRACT_NAME, client_name)[0]
        ledger_records: List[Dict[str, str]] = json.load(result)
        self.losses_distributed: List[Tuple[int, float]] = map(lambda x: x["Loss"], ledger_records)
        self.metrics_distributed: Dict[str, List[Tuple[int, Scalar]]] = map(lambda x: x["CurAccuracy"], ledger_records)
        self.current_fed_session: int = latest_checkpoint["FedSession"] + 1
        self.algorithm: str = algorithm

    def add_loss_distributed(self, server_round: int, loss: float) -> None:
        """Add one loss entry (from distributed evaluation)."""
        self.losses_distributed.append((server_round, loss))

    def add_metrics_distributed(
        self, server_round: int, metrics: Dict[str, Scalar]
    ) -> None:
        """Add metrics entries (from distributed evaluation)."""
        for key in metrics:
            # if not (isinstance(metrics[key], float) or isinstance(metrics[key], int)):
            #     continue  # ignore non-numeric key/value pairs
            if key not in self.metrics_distributed:
                self.metrics_distributed[key] = []
            self.metrics_distributed[key].append((server_round, metrics[key]))

    def post_global_round_model(
            self, server_round: int, parameters: Parameters, ipfs_url: str
    ) -> str:
        """Post a global model to the hyperledger fabric ledger via a smart contract"""
        hash = hash_params(parameters)
        model_id = f"model_{hash}"
        resp = post_model(req_url=f"{GLOBAL_CHECKPOINTS_REQ_URL}create",
                   id=model_id,
                   hash=hash,
                   url=ipfs_url,
                   owner=self.client_name,
                   accuracy=self.metrics_distributed["accuracy"][-1],
                   algorithm=self.algorithm,
                   loss=self.losses_distributed[-1],
                   round=server_round,
                   fed_session=self.current_fed_session,
                   channel_name=CHANNEL_NAME,
                   chaincode_name=CHAINCODE_NAME,
                   contract_name=CONTRACT_NAME,
                   client=self.client_name
        )

        return response_handler(resp)


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
        if self.metrics_distributed:
            rep += "History (metrics, distributed, evaluate):\n" + str(
                self.metrics_distributed
            )
        return rep