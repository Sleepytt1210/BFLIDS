import flwr as fl
import models.net as net
import client as cl
import torch
import data.loader as UNSW 

DEVICE: str = torch.device("cpu")

def main() -> None:
    """Load data, start CifarClient."""

    # Load model and data
    model = net.Net()
    model.to(DEVICE)
    trainloader, testloader, num_examples = UNSW.load_data()

    # Start client
    client = cl.Client(model, trainloader, testloader, num_examples)
    fl.client.start_numpy_client(server_address="localhost:8080", client=client)


if __name__ == "__main__":
    main()